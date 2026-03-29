import json
import subprocess
import webbrowser

from utils.normalize import normalize_text


WEB_SPECIAL_CASES = {
    "youtube": "https://youtube.com",
    "youtube music": "https://music.youtube.com",
    "instagram": "https://instagram.com",
    "hoyolab": "https://www.hoyolab.com",
}

APP_URI_SPECIAL_CASES = {
    "microsoft store": "ms-windows-store:",
    "store": "ms-windows-store:",
}


def _run_powershell_json(script):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0 or not result.stdout.strip():
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _find_start_app_id(app_name):
    query = app_name.replace('"', '`"')
    script = f"""
    $query = "{query}"
    $apps = Get-StartApps | Where-Object {{
        $_.Name -like "*$query*" -or $_.AppID -like "*$query*"
    }} | Select-Object -First 1 Name, AppID
    $apps | ConvertTo-Json -Compress
    """
    data = _run_powershell_json(script)
    if isinstance(data, dict):
        return data.get("AppID")
    return None


def find_start_app_id(app_name):
    normalized_name = normalize_text(app_name)
    return _find_start_app_id(normalized_name)


def _find_appx_family_name(app_name):
    query = app_name.replace('"', '`"')
    script = f"""
    $query = "{query}"
    $package = Get-AppxPackage | Where-Object {{
        $_.Name -like "*$query*" -or
        $_.PackageFamilyName -like "*$query*" -or
        $_.PackageFullName -like "*$query*"
    }} | Select-Object -First 1 Name, PackageFamilyName
    $package | ConvertTo-Json -Compress
    """
    data = _run_powershell_json(script)
    if isinstance(data, dict):
        return data.get("PackageFamilyName")
    return None


def _start_uri(uri):
    result = subprocess.run(
        ["cmd", "/c", "start", "", uri],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def try_special_case_launch(app_name):
    normalized_name = normalize_text(app_name)

    start_app_id = _find_start_app_id(normalized_name)
    if start_app_id and _start_uri(f"shell:AppsFolder\\{start_app_id}"):
        return True

    family_name = _find_appx_family_name(normalized_name)
    if family_name and _start_uri(f"shell:AppsFolder\\{family_name}!App"):
        return True

    if normalized_name in APP_URI_SPECIAL_CASES:
        return _start_uri(APP_URI_SPECIAL_CASES[normalized_name])

    if normalized_name in WEB_SPECIAL_CASES:
        webbrowser.open(WEB_SPECIAL_CASES[normalized_name])
        return True

    return False
