# DuckOS native desktop

The native desktop contains a wlroots compositor and a separate Wayland EGL/GLES shell preview client.

## Compositor

The compositor uses wlroots 0.19 to create a Wayland server, initialize output rendering and manage xdg-shell surfaces. It delegates DRM/KMS and input backends to wlroots on the host.

    meson setup native/desktop/compositor/build native/desktop/compositor
    meson compile -C native/desktop/compositor/build

Run it from a local graphical session with the seat and DRM permissions required by the host's libseat setup:

    WLR_RENDERER=gles2 native/desktop/compositor/build/duckos-compositor

## GPU-backed shell client

The shell preview is a native Wayland xdg-toplevel client in shell/. It creates a wl_egl_window, initializes EGL, binds an OpenGL ES 2 context and draws the workspace panels through GLES. It reports GL_VENDOR, GL_RENDERER and GL_VERSION so a software renderer is not mistaken for hardware acceleration.

    meson setup native/desktop/shell/build native/desktop/shell
    meson compile -C native/desktop/shell/build
    native/desktop/shell/build/duckos-shell

The client needs Wayland client/wayland-egl, wayland-protocols and scanner, EGL and GLESv2 development files. It must run inside a Wayland session.

Known software renderer names are reported as software. Other renderer names are only reported as an active EGL/GLES driver: check the actual GPU device and driver before claiming that rendering is hardware accelerated.

## What this does not mean

The native client is a graphical bring-up, not yet a complete replacement for the existing HTML DuckOS Shell. It currently draws graphical panels but has no text shaping, input actions, launch service, accessibility layer, or settings backend.

The DuckOS bring-up kernel still has no PCI enumeration, DRM/KMS, GPU memory management, command submission, firmware loader, IOMMU integration or vendor GPU driver. The EGL/GLES path can only use host Mesa/DRM when run on a suitable Linux host; it is not GPU acceleration provided by the DuckOS kernel.
