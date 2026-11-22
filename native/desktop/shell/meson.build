project('duckos-shell', 'c',
  version: '0.1.0',
  default_options: ['c_std=c11', 'warning_level=2'])

wayland_client = dependency('wayland-client')
wayland_egl = dependency('wayland-egl')
egl = dependency('egl')
gles = dependency('glesv2')
wayland_protocols = dependency('wayland-protocols')
wayland_scanner = find_program('wayland-scanner')

protocol_dir = wayland_protocols.get_variable(pkgconfig: 'pkgdatadir')
xdg_shell_xml = join_paths(protocol_dir, 'stable', 'xdg-shell', 'xdg-shell.xml')

xdg_shell_header = custom_target('xdg-shell-client-header',
  input: xdg_shell_xml,
  output: 'xdg-shell-client-protocol.h',
  command: [wayland_scanner, 'client-header', '@INPUT@', '@OUTPUT@'])

xdg_shell_code = custom_target('xdg-shell-client-code',
  input: xdg_shell_xml,
  output: 'xdg-shell-protocol.c',
  command: [wayland_scanner, 'private-code', '@INPUT@', '@OUTPUT@'])

executable('duckos-shell',
  ['main.c', xdg_shell_header, xdg_shell_code],
  dependencies: [wayland_client, wayland_egl, egl, gles],
  install: true,
  install_dir: get_option('bindir'))
