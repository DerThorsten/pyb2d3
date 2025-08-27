

function hex_integer_to_html_color(hex) {
    ////console.log("hex_integer_to_html_color", hex);
    const r = (hex >> 16) & 0xFF;
    const g = (hex >> 8) & 0xFF;
    const b = hex & 0xFF;
    ////console.log("hex_integer_to_html_color", r, g, b);
    return `rgb(${r}, ${g}, ${b})`;
}


// add extra function to Context2D to handle hex colors
CanvasRenderingContext2D.prototype.hex_fill_style = function(hex) {
    if(hex === this._hex_fill_style) {
        //console.log('is the same', hex, this._hex_fill_style);
        return; // no need to change if the same
    }
    this.fillStyle = hex_integer_to_html_color(hex);
    this._hex_fill_style = hex;
}
CanvasRenderingContext2D.prototype.hex_stroke_style = function(hex) {
    // if(hex === this._hex_stroke_style){
    //     console.log('is the same', hex, this._hex_stroke_style);
    //     return; // no need to change if the same
    // }
    this.strokeStyle = hex_integer_to_html_color(hex);
    this._hex_stroke_style = hex;
}

function draw_solid_circles(ctx, data_float, data_int, fi, ii) {
    const n_circles = data_int[ii++];
    for (let i = 0; i < n_circles; i++) {
        const x = data_float[fi++];
        const y = data_float[fi++];
        fi++; // skip s and c
        fi++; // skip s and c
        // const s = data_float[fi++];
        // const c = data_float[fi++];
        const radius = data_float[fi++];
        const color = data_int[ii++];
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.hex_fill_style(color);
        ctx.fill();
        ctx.closePath();
    }
    return [fi, ii];
}

function draw_solid_polygons(ctx, data_float, data_int, fi, ii) {
    const n_polygons = data_int[ii++];
    for (let i = 0; i < n_polygons; i++) {
        const n_points = data_int[ii++];
        const color = data_int[ii++];


        const radius = data_float[fi++];
        const tx = data_float[fi++];
        const ty = data_float[fi++];
        const ts = data_float[fi++];
        const tc = data_float[fi++];
        const rot = Math.atan2(ts, tc);

        ctx.hex_fill_style(color);
        ctx.save();
        ctx.translate(tx, ty);
        ctx.rotate(rot);



        if(radius<=0) {
            ctx.beginPath();
            ctx.moveTo(data_float[fi++], data_float[fi++]);
            for(let j = 1; j < n_points ; j++)
            {
                const x = data_float[fi++];
                const y = data_float[fi++];
                ctx.lineTo(x, y);
            }
            ctx.fill();
            ctx.closePath();
        }
        else{

            // step 1:
            // calculate the orientation of the normal of each line segment
            // the first line segment is between point 0 and point 1
            // the last line segment is between point n-1 and point 0

            const points_start = fi;

            let normals = [];

            // get the last point as start point
            let p0_x = data_float[points_start + (n_points - 1) * 2];
            let p0_y = data_float[points_start + (n_points - 1) * 2 + 1];

            for(let j = 0; j < n_points; j++)
            {
                //  next point
                const p1_x = data_float[points_start + j * 2];
                const p1_y = data_float[points_start + j * 2 + 1];

                // delta
                const dx = p1_x - p0_x;
                const dy = p1_y - p0_y;

                // calculate the normal vector
                const nnx = -dy;
                const nny = dx;
                // // normalize the normal vector
                // const length = Math.sqrt(nnx * nnx + nny * nny);
                // const nx = nnx / length;
                // const ny = nny / length;

                // orientation of the normal vector
                const normal_angle = Math.atan2(nny, nnx);

                normals.push(normal_angle);

                // make this point the next last point
                p0_x = p1_x;
                p0_y = p1_y;

            }

            p0_x = data_float[points_start + (n_points - 1) * 2];
            p0_y = data_float[points_start + (n_points - 1) * 2 + 1];
            let n0 = normals[n_points - 1];
            ctx.beginPath();
            for(let j = 0; j < n_points; j++)
            {
                //  next point
                const n1 = normals[j];
                const p1_x = data_float[points_start + j * 2];
                const p1_y = data_float[points_start + j * 2 + 1];

                const offset =  Math.PI;
                ctx.arc(p0_x, p0_y, radius, n0 + offset, n1 + offset, false);

                // make this point the next last point
                p0_x = p1_x;
                p0_y = p1_y;
                n0 = n1;

            }

            fi += n_points * 2; // advance fi

            ctx.closePath();
            ctx.fill();
        }
        ctx.restore();
    }

    return [fi, ii];
}

function draw_solid_capsule(ctx, data_float, data_int, fi, ii) {
    const n_capsules = data_int[ii++];
    for(let i = 0; i < n_capsules; i++) {
        const x1 = data_float[fi++];
        const y1 = data_float[fi++];
        const x2 = data_float[fi++];
        const y2 = data_float[fi++];
        const radius = data_float[fi++];
        const color = data_int[ii++];


        const dx = x2 - x1;
        const dy = y2 - y1;
        const angle = Math.atan2(dx,-dy)
        ctx.beginPath();
        ctx.arc(x1, y1, radius, angle, angle + Math.PI, false);
        ctx.arc(x2, y2, radius, angle + Math.PI, angle + Math.PI * 2, false);
        ctx.closePath();
        ctx.hex_fill_style(color);
        ctx.fill();
        ctx.closePath();
    }
    return [fi, ii];
}

function draw_points(ctx, ppm, data_float, data_int, fi, ii) {
    const n_points = data_int[ii++];
    for(let i = 0; i < n_points; i++) {
        const x = data_float[fi++];
        const y = data_float[fi++];
        const half_size = data_float[fi++] / (2* ppm);
        const color = data_int[ii++];

        // draw rectangle
        ctx.hex_fill_style(color);
        ctx.fillRect(x - half_size, y - half_size, half_size * 2, half_size * 2);

    }
    return [fi,ii];
}

function draw_polygons(ctx, data_float, data_int, fi, ii) {
    const n_polygons = data_int[ii++];
    for (let i = 0; i < n_polygons; i++) {
        const n_points = data_int[ii++];
        const color = data_int[ii++];

        ctx.hex_stroke_style(color);
        ctx.beginPath();

        const points_start = fi;
        for(let j = 0; j < n_points; j++) {
            const x = data_float[fi++];
            const y = data_float[fi++];
            if(j === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();
        ctx.fill();
    }

    return [fi, ii];
}

function draw_circles(ctx, data_float, data_int, fi, ii) {
    const n_circles = data_int[ii++];
    for (let i = 0; i < n_circles; i++) {
        const x = data_float[fi++];
        const y = data_float[fi++];
        const r = data_float[fi++];

        const color = data_int[ii++];
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.hex_stroke_style(color);
        ctx.stroke();
        ctx.closePath();
    }

    return [fi, ii];
}

function draw_segments(ctx, data_float, data_int, fi, ii) {
    const n_segments = data_int[ii++];
    for (let i = 0; i < n_segments; i++) {
        const x1 = data_float[fi++];
        const y1 = data_float[fi++];
        const x2 = data_float[fi++];
        const y2 = data_float[fi++];
        const color = data_int[ii++];
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.hex_stroke_style(color);
        ctx.stroke();
        ctx.closePath();
    }

    return [fi, ii];
}



function clear_canvas(ctx, canvas) {
    // clear the canvas
    ctx.hex_fill_style(0x2e2e2e);
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}



function on_custom_message(model, canvas, ctx, msg) {

    let time_start = performance.now();

    let fi =0;
    let ii = 0;

    // It can be used to update the canvas or perform other actions
    const int_array = msg[0];
    const mode = int_array[ii++];
    if(mode === 1) {
        // just clear
        clear_canvas(ctx, canvas);
        return;
    }
    const float_array = msg[1];




    // This function is called when a custom message is received

    const ppm = float_array[fi++];
    const offset_x = float_array[fi++];
    const offset_y = float_array[fi++];


    // clear the canvas
    clear_canvas(ctx, canvas);

    // begin drawing
    ctx.save();
    ctx.translate(0, canvas.height);
    ctx.scale(ppm, -ppm);
    ctx.translate(offset_x, offset_y);
    ctx.lineWidth = 1 / ppm;
    ctx.ppm = ppm;
    ctx.offset_x = offset_x;
    ctx.offset_y = offset_y;


    [fi, ii] = draw_solid_circles(ctx, float_array, int_array, fi, ii);
    [fi, ii] = draw_solid_polygons(ctx, float_array, int_array, fi, ii);
    [fi, ii] = draw_solid_capsule(ctx, float_array, int_array, fi, ii);
    [fi, ii] = draw_points(ctx, ppm, float_array, int_array, fi, ii);
    [fi, ii] = draw_polygons(ctx, float_array, int_array, fi, ii);
    [fi, ii] = draw_circles(ctx, float_array, int_array, fi, ii);
    [fi, ii] = draw_segments(ctx, float_array, int_array, fi, ii);

    // end drawing
    ctx.restore();

    let time_end = performance.now();
    let time_diff = time_end - time_start;
    let hertz = 1000 / time_diff;

    // draw the time to the canvas

    //  white in hex
    ctx.hex_fill_style(0xFFFFFF);
    ctx.font = "16px Arial";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText(`Render time: ${time_diff.toFixed(2)} ms (${hertz.toFixed(2)} Hz)`, 10, 10);

    model.set("_frame", model.get("_frame") + 1);
    model.save_changes();

}


function client_to_world(canvas, ctx, clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const canvasX = (clientX - rect.left) * scaleX;
    const canvasY = (clientY - rect.top) * scaleY;

    const worldX = (canvasX / ctx.ppm) - ctx.offset_x;
    const worldY = -((canvasY - canvas.height) / ctx.ppm) - ctx.offset_y;
    return [worldX, worldY];

}


function map_key(key){
    if (key == " ") {
        return "space";
    }
    if(key == "Control") {
        return "ctrl";
    }
    if(key == "Shift") {
        return "shift";
    }
    if(key == "Meta") {
        return "meta";
    }
    if(key == "Alt") {
        return "alt";
    }
    return key.toLowerCase();
}

function setup_event_listeners(model,ctx, canvas) {

    canvas._last_client = undefined;
    canvas._mouse_down = false;
    canvas._mouse_inside = true;

    // handle events
    canvas.addEventListener("click", (event) => {
        // focus canvas
        canvas.focus();
        const [world_x, world_y] = client_to_world(canvas, ctx, event.clientX, event.clientY);
        model.send(["click", world_x, world_y]);
        canvas._last_client = [event.clientX, event.clientY];
    });

    // mouse down event
    canvas.addEventListener("mousedown", (event) => {
        // focus canvas
        canvas.focus();
        const [world_x, world_y] = client_to_world(canvas, ctx, event.clientX, event.clientY);
        model.send(["mouse_down",world_x, world_y]);
        canvas._last_client = [event.clientX, event.clientY];
        canvas._mouse_down = true;
    });

    // mouse up event
    canvas.addEventListener("mouseup", (event) => {
        const [world_x, world_y] = client_to_world(canvas, ctx, event.clientX, event.clientY);
        model.send(["mouse_up", world_x, world_y]);
        canvas._last_client = [event.clientX, event.clientY];
        canvas._mouse_down = false;
    });

    // mouse move event
    canvas.addEventListener("mousemove", (event) => {
        // only send mouse move if mouse is down and mouse is inside the canvas
        if (!canvas._mouse_down || !canvas._mouse_inside) {
            return;
        }
        if (canvas._last_client === undefined) {
            // do nothing
            canvas._last_client = [event.clientX, event.clientY];
            return;
        }
        const [world_x, world_y] = client_to_world(canvas, ctx, event.clientX, event.clientY);

        const [last_client_x, last_client_y] = canvas._last_client;
        const [client_x, client_y] = [event.clientX, event.clientY];

        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        const client_dx = client_x - last_client_x;
        const client_dy = client_y - last_client_y;


        const canvas_dx = client_dx * scaleX;
        const canvas_dy = client_dy * scaleY;
        const abs_sum =  Math.abs(canvas_dx) + Math.abs(canvas_dy);
        if( Math.abs(canvas_dx) + Math.abs(canvas_dy) <= 3) {
            return;
        }

        const world_delta_x = canvas_dx / ctx.ppm;
        const world_delta_y = -1 * canvas_dy / ctx.ppm;

        // console.log(`Mouse move at world coordinates: (${world_x}, ${world_y}) with delta (${world_delta_x}, ${world_delta_y})`);

        canvas._last_client = [event.clientX, event.clientY];

        model.send(["mouse_move", world_x, world_y, world_delta_x, world_delta_y]);

    });


    // mouse wheel event
    canvas.addEventListener("wheel", (event) => {
        // Prevent the default scrolling behavior
        event.preventDefault();
        const [world_x, world_y] = client_to_world(canvas, ctx, event.clientX, event.clientY);

        model.send([ "mouse_wheel",  world_x, world_y, event.deltaY ]);
    });


    // mouse leave event
    canvas.addEventListener("mouseleave", (event) => {
        // console.log("Mouse left the canvas");
        canvas._last_client = undefined; // reset last client position
        model.send(["mouse_leave"]);
        canvas._mouse_inside = false; // set mouse inside to false
        canvas._mouse_down = false; // reset mouse down state
    });

    // mouse enter event
    canvas.addEventListener("mouseenter", (event) => {
        // console.log("Mouse entered the canvas");
        canvas._last_client = undefined; // reset last client position
        model.send(["mouse_enter"]);
        canvas._mouse_inside = true; // set mouse inside to true
    });




    // key-down event
    canvas.addEventListener("keydown", (event) => {

        event.preventDefault();
        event.stopPropagation();
        model.send(["key_down",
            map_key(event.key),
            event.ctrlKey,
            event.shiftKey,
            event.metaKey,
            event.altKey
        ]);
    });

    // key-up event
    canvas.addEventListener("keyup", (event) => {

        event.preventDefault();
        event.stopPropagation();
        model.send(["key_up",
            map_key(event.key)
        ]);
    });

}

function render({ model, el }) {

    // create a canvas element
    let canvas = document.createElement("canvas");

    canvas.setAttribute("tabindex", "0"); // make the canvas focusable
    // canvas.style.outline = "none"; // remove focus outline

    canvas.width = model.get("_width");
    canvas.height = model.get("_height");
    canvas.style.width = "100%";
    canvas.style.height = "auto";
    el.appendChild(canvas);



    // draw a rectangle in blue
    let ctx = canvas.getContext("2d", {
        willReadFrequently: false, // we don't need to read pixels frequently
        alpha: false, // no transparency
        desynchronized: true // for performance
    });
    ctx._hex_fill_style = 0
    ctx._hex_stroke_style = 0;
    ctx.strokeStyle = hex_integer_to_html_color(ctx._hex_stroke_style);
    ctx.fillStyle = hex_integer_to_html_color(ctx._hex_fill_style);
    ctx.ppm = 1;
    ctx.offset_x = 0;
    ctx.offset_y = 0;
    ctx.fillRect(0, 0, canvas.width, canvas.height);


    // on custom message, draw a rectangle in red
    model.on("msg:custom", (msg) => {
        try {
            on_custom_message(model, canvas, ctx, msg);
        } catch (error) {
            console.error("Error handling custom message:", error);
        }
    });

    // setup event listeners
    setup_event_listeners(model, ctx, canvas);



}
export default { render };
