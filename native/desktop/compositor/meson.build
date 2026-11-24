project('duckos-compositor', 'c',
  version: '0.1.0',
  default_options: ['c_std=c11', 'warning_level=2'])

wayland_server = dependency('wayland-server')
wlroots = dependency('wlroots-0.19', version: '>=0.19.2')
threads = dependency('threads')
wayland_protocols = dependency('wayland-protocols', version: '>=1.25')
wayland_scanner = find_program('wayland-scanner')
wayland_protocols_datadir = wayland_protocols.get_variable(pkgconfig: 'pkgdatadir')
xdg_shell_xml = wayland_protocols_datadir / 'stable/xdg-shell/xdg-shell.xml'

xdg_shell_server_header = custom_target('xdg-shell-server-header',
  input: xdg_shell_xml,
  output: 'xdg-shell-protocol.h',
  command: [wayland_scanner, 'server-header', '@INPUT@', '@OUTPUT@'])
xdg_shell_private_code = custom_target('xdg-shell-private-code',
  input: xdg_shell_xml,
  output: 'xdg-shell-protocol.c',
  command: [wayland_scanner, 'private-code', '@INPUT@', '@OUTPUT@'],
  depends: [xdg_shell_server_header])

executable('duckos-compositor',
  'main.c',
  xdg_shell_server_header,
  xdg_shell_private_code,
  dependencies: [wayland_server, wlroots, threads],
  c_args: ['-DWLR_USE_UNSTABLE'],
  install: true,
  install_dir: get_option('bindir'))
