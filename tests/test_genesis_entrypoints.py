import subprocess
import sys

def test_notice_is_silent():
    res = subprocess.run([sys.executable, "-c", "import pgsafe._genesis; pgsafe._genesis.print_upgrade_notice()"], capture_output=True, text=True)
    assert res.stderr == ""
    assert res.stdout == ""
    import pgsafe._genesis
    assert pgsafe._genesis.NOTICE == ""
