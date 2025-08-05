


OffscreenCanvasRenderingContext2D.prototype._begin_draw = function (
    ppm,
    offset_x,
    offset_y,
)
{
    ////console.log("OffscreenCanvasRenderingContext2D._begin_draw", ppm, offset_x, offset_y);

    // set scale
    this.save();
    this.translate(0, this.canvas.height);
    this.scale(ppm, -ppm);
    // set offset
    this.translate(offset_x, offset_y);


    // set the line with to the inverse
    this.lineWidth = 1 / ppm;
    this.ppm = ppm;
};

OffscreenCanvasRenderingContext2D.prototype._end_draw = function () {
    ////console.log("OffscreenCanvasRenderingContext2D._end_draw");
    // restore
    this.restore();
}


function hex_integer_to_html_color(hex) {
    ////console.log("hex_integer_to_html_color", hex);
    const r = (hex >> 16) & 0xFF;
    const g = (hex >> 8) & 0xFF;
    const b = hex & 0xFF;
    ////console.log("hex_integer_to_html_color", r, g, b);
    return `rgb(${r}, ${g}, ${b})`;
}


// cirlces
OffscreenCanvasRenderingContext2D.prototype._draw_circles = function( data) {
    ////console.log("OffscreenCanvasRenderingContext2D._draw_circles", data);
    const ctx = this;

    len = data.length / 4;
    for (let i = 0; i < len; i++)
    {
        const index = i * 4;
        const x = data[index + 0];
        const y = data[index + 1];
        const radius = data[index + 2];
        const color = data[index + 3];

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.strokeStyle = hex_integer_to_html_color(color);
        ctx.stroke();
        ctx.closePath();
    }
}

// solid circles
OffscreenCanvasRenderingContext2D.prototype._draw_solid_circles = function(data) {
    ////console.log("OffscreenCanvasRenderingContext2D._draw_solid_circles", data);
    const ctx = this;

    len = data.length / 6;
    for (let i = 0; i < len; i++)
    {
        const index = i * 6;
        const x = data[index + 0];
        const y = data[index + 1];
        // const s = data[index + 2];
        // const c = data[index + 3];
        const radius = data[index + 4];
        const color = data[index + 5];

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = hex_integer_to_html_color(color);
        ctx.fill();
        ctx.closePath();

    }
}

// polygons
OffscreenCanvasRenderingContext2D.prototype._draw_polygons = function(n_items, data) {

    last_index = 0;
    for(let i = 0; i < n_items; i++)
    {
        const n_points = data[last_index];
        const color = data[last_index + 1];

        this.strokeStyle = hex_integer_to_html_color(color);

        this.beginPath();
        this.moveTo(data[last_index + 2], data[last_index + 3]);
        for(let j = 1; j < n_points ; j++)
        {
            const index = last_index + 2 + j * 2;
            const x = data[index];
            const y = data[index + 1];
            this.lineTo(x, y);
        }
        this.closePath();
        this.stroke();
        last_index += 2 + n_points * 2;
    }
}


OffscreenCanvasRenderingContext2D.prototype._draw_solid_polygons = function(n_items, data) {
    last_index = 0;
    for(let i = 0; i < n_items; i++)
    {
        const n_points = data[last_index];
        const radius = data[last_index + 1];
        const color = data[last_index + 2];
        const tx = data[last_index + 3];
        const ty = data[last_index + 4];
        const ts = data[last_index + 5];
        const tc = data[last_index + 6];

        // get rot from ts (sine) and tc (cosine)
        const rot = Math.atan2(ts, tc);

        this.fillStyle = hex_integer_to_html_color(color);


        this.save();
        this.translate(tx, ty);
        this.rotate(rot);

        if(radius<=0) {
            this.beginPath();
            this.moveTo(data[last_index + 7], data[last_index + 8]);
            for(let j = 1; j < n_points ; j++)
            {
                const index = last_index + 7 + j * 2;
                const x = data[index];
                const y = data[index + 1];
                this.lineTo(x, y);
            }
            this.fill();
            this.closePath();
        }
        else{
            // step 1:
            // calculate the orientation of the normal of each line segment
            // the first line segment is between point 0 and point 1
            // the last line segment is between point n-1 and point 0

            const points_start = last_index + 7;

            let normals = [];

            // get the last point as start point
            let p0_x = data[points_start + (n_points - 1) * 2];
            let p0_y = data[points_start + (n_points - 1) * 2 + 1];

            for(let j = 0; j < n_points; j++)
            {
                //  next point
                const p1_x = data[points_start + j * 2];
                const p1_y = data[points_start + j * 2 + 1];

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

            p0_x = data[points_start + (n_points - 1) * 2];
            p0_y = data[points_start + (n_points - 1) * 2 + 1];
            n0 = normals[n_points - 1];
            this.beginPath();
            for(let j = 0; j < n_points; j++)
            {
                //  next point
                const n1 = normals[j];
                const p1_x = data[points_start + j * 2];
                const p1_y = data[points_start + j * 2 + 1];

                const offset =  Math.PI;
                this.arc(p0_x, p0_y, radius, n0 + offset, n1 + offset, false);

                // make this point the next last point
                p0_x = p1_x;
                p0_y = p1_y;
                n0 = n1;

            }

            this.closePath();
            this.fill();
        }

        this.restore();
        last_index += 7 + n_points * 2;
    }
}
// segments
OffscreenCanvasRenderingContext2D.prototype._draw_segments = function(data) {
    ////console.log("OffscreenCanvasRenderingContext2D._draw_segments", data);
    const ctx = this;

    len = data.length / 5;
    for (let i = 0; i < len; i++)
    {
        const index = i * 5;
        const x1 = data[index + 0];
        const y1 = data[index + 1];
        const x2 = data[index + 2];
        const y2 = data[index + 3];
        const color = data[index + 4];

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = hex_integer_to_html_color(color);
        ctx.stroke();
        ctx.closePath();
    }
}

OffscreenCanvasRenderingContext2D.prototype._draw_solid_capsules = function(data) {
    ////console.log("OffscreenCanvasRenderingContext2D._draw_capsules", data);
    const ctx = this;

    len = data.length / 6;
    for (let i = 0; i < len; i++)
    {
        const index = i * 6;
        const x1 = data[index + 0];
        const y1 = data[index + 1];
        const x2 = data[index + 2];
        const y2 = data[index + 3];
        const radius = data[index + 4];
        const color = data[index + 5];
        const dx = x2 - x1;
        const dy = y2 - y1;
        const angle = Math.atan2(dx,-dy)
        ctx.beginPath();
        ctx.arc(x1, y1, radius, angle, angle + Math.PI, false);
        ctx.arc(x2, y2, radius, angle + Math.PI, angle + Math.PI * 2, false);
        ctx.closePath();
        ctx.fillStyle = hex_integer_to_html_color(color);
        ctx.fill();
        ctx.closePath();
    }
}

// draw points
OffscreenCanvasRenderingContext2D.prototype._draw_points = function(data) {
    ////console.log("OffscreenCanvasRenderingContext2D._draw_points", data);
    const ctx = this;

    len = data.length / 4;
    for (let i = 0; i < len; i++)
    {
        const index = i * 4;
        const x = data[index + 0];
        const y = data[index + 1];
        const size = data[index + 2] / this.ppm
        const color = data[index + 3];

        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fillStyle = hex_integer_to_html_color(color);
        ctx.fill();
        ctx.closePath();
    }
}
