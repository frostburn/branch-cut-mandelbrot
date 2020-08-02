from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef(
    "int mandelbrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom, double exponent, double *cuts, int max_iterations);"
)

ffibuilder.set_source(
    "_routines",
    """
    int escape_time(double *cx, double *cy, double exponent, double *cuts, int max_iterations) {
        double tau = 2*M_PI;
        double i_tau = 1.0 / tau;
        double x = cx[0];
        double y = cy[0];
        double magnitude, phase;
        for (int i = 0; i < max_iterations; i++) {
            magnitude = x*x + y*y;
            if (magnitude > 10000) {
                cx[0] = x;
                cy[0] = y;
                return i;
            }
            phase = (atan2(y, x) + cuts[i])*i_tau;
            phase = ((phase-floor(phase))*tau - cuts[i]) * exponent;
            magnitude = pow(magnitude, exponent*0.5);
            x = cos(phase)*magnitude + cx[0];
            y = sin(phase)*magnitude + cy[0];
        }
        cx[0] = x;
        cy[0] = y;
        return max_iterations;
    }

    int mandelbrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom, double exponent, double *cuts, int max_iterations) {
        zoom = pow(2, -zoom) / height;
        for (size_t i = 0; i < width * height; i++) {
            double x = (i % width);
            double y = (i / width);
            x = (2 * x - width) * zoom + center_x;
            y = (2 * y - height) * zoom + center_y;

            out[i] = escape_time(&x, &y, exponent, cuts, max_iterations);
            if (out[i] < max_iterations) {
                out[i] -= log(log(x*x + y*y)*0.5)/log(fabs(exponent));
            }
        }
        return 0;
    }
    """
)

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
