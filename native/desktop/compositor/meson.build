project('duckos-compositor', 'c',
  version: '0.1.0',
  default_options: ['c_std=c11', 'warning_level=2'])

wayland_server = dependency('wayland-server')
wayland_protocols = dependency('wayland-protocols', version: '>=1.41')
wlroots = dependency('wlroots-0.19', version: '>=0.19.2')
threads = dependency('threads')
wayland_scanner = find_program('wayland-scanner')

# wlroots exposes the xdg-shell API but expects consumers to generate this
# protocol header and add its build directory to the include path.
xdg_shell_protocol_h = custom_target(
  'xdg-shell-protocol-header',
  input: wayland_protocols.get_variable(pkgconfig: 'pkgdatadir') / 'stable/xdg-shell/xdg-shell.xml',
  output: 'xdg-shell-protocol.h',
  command: [wayland_scanner, 'server-header', '@INPUT@', '@OUTPUT@'])

executable('duckos-compositor',
  ['main.c', xdg_shell_protocol_h],
  dependencies: [wayland_server, wayland_protocols, wlroots, threads],
  c_args: ['-DWLR_USE_UNSTABLE'],
  install: true,
  install_dir: get_option('bindir'))
