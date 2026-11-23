# DuckOS native shell client

The native shell client is a Wayland xdg-toplevel application. It creates an EGL window surface backed by Wayland, binds an OpenGL ES 2 context and draws the DuckOS workspace layout using GPU-driver-backed GLES clear/scissor operations.

Build it with the Meson project in this directory:

    meson setup build .
    meson compile -C build

Required development packages include Wayland client, wayland-egl, wayland-protocols, wayland-scanner, EGL and GLESv2.

Run it inside a Wayland session:

    ./build/duckos-shell

At startup the program prints GL_VENDOR, GL_RENDERER and GL_VERSION. Known software renderers such as llvmpipe, softpipe, swrast and SwiftShader are labelled as software. Other renderers are reported as an active EGL/GLES driver; the actual device and driver must still be checked before claiming hardware acceleration.

This is a graphical bring-up client, not yet the complete browser DuckOS interface. It has no text shaping, input actions, application launcher, settings backend, or accessibility layer. The wlroots compositor must also provide an output and a running backend. The current native kernel does not have DRM/KMS or a GPU driver, so this client can currently demonstrate hardware acceleration only when run on a suitable Linux host.
