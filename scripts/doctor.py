"""Self-check after install: Python version, TikHub key + balance, free fallback tools.

  python3 scripts/doctor.py              check everything
  python3 scripts/doctor.py --save-key   read a TikHub key from stdin and store it in ~/.config/tikhub/key (600)
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

KEY_PATH = os.path.expanduser('~/.config/tikhub/key')


def save_key():
    key = sys.stdin.readline().strip()
    if len(key) < 20:
        sys.exit('没有读到有效的 Key（太短）。请把完整的 TikHub API Key 通过标准输入传进来。')
    os.makedirs(os.path.dirname(KEY_PATH), exist_ok=True)
    fd = os.open(KEY_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(key)
    os.chmod(KEY_PATH, 0o600)
    print(f'已保存到 {KEY_PATH}（仅本机用户可读）。')


def tool_version(cmd):
    if not shutil.which(cmd[0]):
        return None
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0][:60] if (out.stdout or out.stderr) else '已安装'
    except Exception:
        return '已安装'


def main():
    if '--save-key' in sys.argv:
        save_key()
        return
    ok = True
    print('competitor-kol-radar 自检\n')

    v = sys.version_info
    if v >= (3, 9):
        print(f'✅ Python {v.major}.{v.minor}')
    else:
        ok = False
        print(f'❌ Python {v.major}.{v.minor}：需要 3.9 以上。macOS 可运行 `brew install python`，Windows 到 python.org 下载。')

    has_key = bool(os.environ.get('TIKHUB_API_KEY') or os.path.exists(KEY_PATH))
    if has_key:
        import tikhub
        bal, err = tikhub.balance()
        if bal is not None:
            tip = '，余额偏低，一次海外调研约 $0.5–1' if bal < 1 else ''
            print(f'✅ TikHub Key 有效，余额 ${bal:.2f}{tip}')
        else:
            ok = False
            print(f'❌ TikHub Key 无法使用（{err}）。到 https://tikhub.io 后台确认 Key 是否正确、是否过期，再重新保存。')
    else:
        print('⚠️  没有 TikHub Key：可以先用免费兜底方案（数据少一些），或到 https://tikhub.io 注册拿 Key，'
              '然后把 Key 发给 Agent 保存。')

    yt = tool_version(['yt-dlp', '--version'])
    xhs = tool_version(['xhs', '--version'])
    print(f"{'✅' if yt else '➖'} yt-dlp（免费兜底：YouTube / TikTok）{'：' + yt if yt else '未安装，可选：pipx install yt-dlp 或 brew install yt-dlp'}")
    print(f"{'✅' if xhs else '➖'} xhs-cli（免费兜底：小红书）{'：' + xhs if xhs else '未安装，可选：pipx install xiaohongshu-cli，然后 xhs login'}")

    print('\n' + ('一切就绪。对 Agent 说："帮我拆一下 <品牌名> 最近 3 个月的海外红人营销"。' if ok and (has_key or yt) else
                  '还有项目没准备好，按上面的提示处理；没有 TikHub 也能用免费兜底先跑。'))


if __name__ == '__main__':
    main()
