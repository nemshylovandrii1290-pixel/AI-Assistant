import json
import subprocess
import webbrowser


def _find_start_app_id(app_name):
    script = f"""
    $query = "{app_name.replace('"', '`"')}"
    $apps = Get-StartApps | Where-Object {{ $_.Name -like "*$query*" }}
    $apps | Select-Object Name, AppID | ConvertTo-Json -Compress
    """

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0 or not result.stdout.strip():
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    if isinstance(data, list):
        if not data:
            return None
        return data[0].get("AppID")

    return data.get("AppID")


def try_special_case_launch(app_name):
    start_app_id = _find_start_app_id(app_name)
    if start_app_id:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f'Start-Process "shell:AppsFolder\\{start_app_id}"'
            ],
            check=False
        )
        return True

    if app_name in ["youtube", "ютуб"]:
        webbrowser.open("https://youtube.com")
        return True

    if app_name in ["youtube music", "ютуб музика", "ютуб музик"]:
        webbrowser.open("https://music.youtube.com")
        return True

    if app_name in ["instagram", "інстаграм"]:
        webbrowser.open("https://instagram.com")
        return True

    return False
