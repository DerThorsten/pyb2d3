#pragma once
#include <atomic>
#include <cmath>
#include <condition_variable>
#include <functional>
#include <future>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <thread>
#include <vector>

enum class NumThreads : int
{
    Auto = -1,     ///< Determine number of threads automatically (from
                   ///< <tt>std::thread::hardware_concurrency()</tt>)
    Nice = -2,     ///< Use half as many threads as <tt>Auto</tt> would.
    NoThreads = 0  ///< Switch off multi-threading (i.e. execute tasks sequentially)
};

class ParallelOptions
{
public:


    ParallelOptions(int nT = static_cast<int>(NumThreads::Auto))
        : numThreads_(actualNumThreads(nT))
    {
    }

    int getNumThreads() const
    {
        return numThreads_;
    }

    int getActualNumThreads() const
    {
        return std::max(1, numThreads_);
    }

    ParallelOptions& numThreads(const int n)
    {
        numThreads_ = actualNumThreads(n);
        return *this;
    }


private:

    // helper function to compute the actual number of threads
    static std::size_t actualNumThreads(const int userNThreads)
    {
#ifdef NIFTY_NO_PARALLELISM
        return 0;
#else
        return userNThreads >= 0                                    ? userNThreads
               : userNThreads == static_cast<int>(NumThreads::Nice) ? std::thread::hardware_concurrency() / 2
                                                                    : std::thread::hardware_concurrency();
#endif
    }

    int numThreads_;
};

// The class Threadpool is based on:
// https://github.com/progschj/ThreadPool/
// with the crucial difference that any
// enqueued function get a consecutive worker
// index as argument.
// This allows for ``thread-private`` / per-thread-storage
//
// The implementation of https://github.com/progschj/ThreadPool/
// has the following copyright notice:
//
// Copyright (c) 2012 Jakob Progsch, Václav Zeman
//
// This software is provided 'as-is', without any express or implied
// warranty. In no event will the authors be held liable for any damages
// arising from the use of this software.
//
// Permission is granted to anyone to use this software for any purpose,
// including commercial applications, and to alter it and redistribute it
// freely, subject to the following restrictions:
//
//   1. The origin of this software must not be misrepresented; you must not
//   claim that you wrote the original software. If you use this software
//   in a product, an acknowledgment in the product documentation would be
//   appreciated but is not required.
//
//   2. Altered source versions must be plainly marked as such, and must not be
//   misrepresented as being the original software.
//
//   3. This notice may not be removed or altered from any source
//   distribution.
//
//

class ThreadPool
{
public:

    ~ThreadPool();

    ThreadPool(const ParallelOptions& options)
        : stop(false)
        , busy(0)
        , processed(0)
    {
        init(options);
    }

    ThreadPool(const int n)
        : stop(false)
        , busy(0)
        , processed(0)
    {
        init(ParallelOptions().numThreads(n));
    }


    template <class F>
    std::future<typename std::result_of<F(int)>::type> enqueueReturning(F&& f);


    template <class F>
    std::future<void> enqueue(F&& f);

    void waitFinished()
    {
        std::unique_lock<std::mutex> lock(queue_mutex);
        finish_condition.wait(
            lock,
            [this]()
            {
                return tasks.empty() && (busy == 0);
            }
        );
    }

    std::size_t nThreads() const
    {
        return workers.size();
    }

private:

    // helper function to init the thread pool
    void init(const ParallelOptions& options);

    // need to keep track of threads so we can join them
    std::vector<std::thread> workers;

    // the task queue
    std::queue<std::function<void(int)>> tasks;

    // synchronization
    std::mutex queue_mutex;
    std::condition_variable worker_condition;
    std::condition_variable finish_condition;
    bool stop;
    std::atomic<unsigned int> busy, processed;
};

inline void ThreadPool::init(const ParallelOptions& options)
{
    const std::size_t actualNThreads = options.getNumThreads();
    for (std::size_t ti = 0; ti < actualNThreads; ++ti)
    {
        workers.emplace_back(
            [ti, this]
            {
                for (;;)
                {
                    std::function<void(int)> task;
                    {
                        std::unique_lock<std::mutex> lock(this->queue_mutex);

                        // will wait if : stop == false  AND queue is empty
                        // if stop == true AND queue is empty thread function will return later
                        //
                        // so the idea of this wait, is : If where are not in the destructor
                        // (which sets stop to true, we wait here for new jobs)
                        this->worker_condition.wait(
                            lock,
                            [this]
                            {
                                return this->stop || !this->tasks.empty();
                            }
                        );
                        if (!this->tasks.empty())
                        {
                            ++busy;
                            task = std::move(this->tasks.front());
                            this->tasks.pop();
                            lock.unlock();
                            task(ti);
                            ++processed;
                            --busy;
                            finish_condition.notify_one();
                        }
                        else if (stop)
                        {
                            return;
                        }
                    }
                }
            }
        );
    }
}

inline ThreadPool::~ThreadPool()
{
    {
        std::unique_lock<std::mutex> lock(queue_mutex);
        stop = true;
    }
    worker_condition.notify_all();
    for (std::thread& worker : workers)
    {
        worker.join();
    }
}

template <class F>
inline std::future<typename std::result_of<F(int)>::type> ThreadPool::enqueueReturning(F&& f)
{
    typedef typename std::result_of<F(int)>::type result_type;
    typedef std::packaged_task<result_type(int)> PackageType;

    auto task = std::make_shared<PackageType>(f);
    auto res = task->get_future();

    if (workers.size() > 0)
    {
        {
            std::unique_lock<std::mutex> lock(queue_mutex);

            // don't allow enqueueing after stopping the pool
            if (stop)
            {
                throw std::runtime_error("enqueue on stopped ThreadPool");
            }

            tasks.emplace(
                [task](int tid)
                {
                    (*task)(tid);
                }
            );
        }
        worker_condition.notify_one();
    }
    else
    {
        (*task)(0);
    }

    return res;
}

template <class F>
inline std::future<void> ThreadPool::enqueue(F&& f)
{
    typedef std::packaged_task<void(int)> PackageType;

    auto task = std::make_shared<PackageType>(f);
    auto res = task->get_future();
    if (workers.size() > 0)
    {
        {
            std::unique_lock<std::mutex> lock(queue_mutex);

            // don't allow enqueueing after stopping the pool
            if (stop)
            {
                throw std::runtime_error("enqueue on stopped ThreadPool");
            }

            tasks.emplace(
                [task](int tid)
                {
                    (*task)(tid);
                }
            );
        }
        worker_condition.notify_one();
    }
    else
    {
        (*task)(0);
    }
    return res;
}
