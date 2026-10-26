"""Narrow user PATH ownership; never modify execution policy or the parent shell."""
import json
import os
from pathlib import Path
import shlex
from . import environment, state

START = '# >>> Aikya managed PATH >>>\n'
END = '# <<< Aikya managed PATH <<<\n'


def ensure_user_path(bin_dir, enabled=True, root=None):
    if not enabled:return {'changed':False}
    root = Path(root or environment.app_root())
    marker = state.safe(root/'user-path.json')
    if marker.exists():return json.loads(marker.read_text())
    bin_dir = Path(bin_dir).absolute()
    if os.name == 'nt':return ensure_windows_path(str(bin_dir),marker)
    shell=Path(os.environ.get('SHELL','')).name
    if shell not in ('bash','zsh'):
        print('Add to your shell PATH: '+str(bin_dir));return {'changed':False}
    profile=state.safe(Path.home()/('.zshrc' if shell=='zsh' else '.bashrc'))
    before=profile.read_bytes() if profile.exists() else b''
    if START.encode() in before:raise ValueError('Unowned or modified Aikya PATH block requires review')
    prefix=b'' if not before or before.endswith(b'\n') else b'\n'
    block=(START+'export PATH='+shlex.quote(str(bin_dir))+':"$PATH"\n'+END).encode()
    record={'platform':'posix','profile':str(profile),'block':block.decode(),'prefix':prefix.decode()}
    state.write_json(marker,record)
    profile.parent.mkdir(parents=True,exist_ok=True)
    profile.write_bytes(before+prefix+block)
    return record


def remove_user_path(root):
    marker=state.safe(Path(root)/'user-path.json')
    if not marker.exists():return
    record=json.loads(marker.read_text())
    if record['platform']=='windows':
        if not remove_windows_path(record):return
    else:
        profile=state.safe(Path(record['profile']))
        if profile.parent != Path.home() or profile.name not in ('.zshrc','.bashrc'):
            raise ValueError('Unowned PATH profile')
        block=record['block'].encode()
        if not profile.exists():return
        actual=profile.read_bytes()
        if actual.count(block)!=1:
            print('Preserved modified user PATH block');return
        profile.write_bytes(actual.replace(record['prefix'].encode()+block,b'',1))
    marker.unlink()


def ensure_windows_path(entry, marker):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,'Environment') as key:
        try:before,kind=winreg.QueryValueEx(key,'Path')
        except FileNotFoundError:before,kind='',winreg.REG_EXPAND_SZ
        if entry.casefold() in [x.casefold() for x in before.split(';')]:return {'changed':False}
        record={'platform':'windows','entry':entry,'kind':kind}
        state.write_json(marker,record)
        winreg.SetValueEx(key,'Path',0,kind,before+(';' if before else '')+entry)
    notify_environment_change()
    return record


def remove_windows_path(record):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,'Environment') as key:
        try:value,kind=winreg.QueryValueEx(key,'Path')
        except FileNotFoundError:return False
        entries=value.split(';')
        if entries.count(record['entry'])!=1:return False
        entries.remove(record['entry']);winreg.SetValueEx(key,'Path',0,kind,';'.join(entries))
    notify_environment_change()
    return True


def notify_environment_change():
    """Notify new GUI-launched shells after changing HKCU Environment, not HKLM."""
    import ctypes
    from ctypes import wintypes
    try:
        send=ctypes.WinDLL('user32',use_last_error=True).SendMessageTimeoutW
        send.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPCWSTR,
                       wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)]
        send.restype=wintypes.LPARAM
        result=ctypes.c_size_t()
        notified=bool(send(0xFFFF,0x001A,0,'Environment',0x0002,2000,ctypes.byref(result)))
    except (AttributeError,OSError):
        notified=False
    if not notified and os.name=='nt':
        print('User PATH saved; sign out and back in if new applications retain the previous PATH.')
    return notified
