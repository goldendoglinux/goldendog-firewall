import os
import subprocess
import tempfile


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_helper_path():
    system_helper = "/usr/libexec/goldendog-firewall/ufw-apply"
    dev_helper = os.path.join(SCRIPT_DIR, "..", "helpers", "ufw-apply")

    if os.path.exists(system_helper):
        return system_helper
    if os.path.exists(dev_helper):
        return dev_helper
    return ""


def _resolve_ufw_bin():
    candidates = ["/usr/sbin/ufw", "/sbin/ufw", "/usr/bin/ufw"]
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return "ufw"


def list_network_interfaces():
    """Return interface names for dropdowns, excluding loopback."""
    base = "/sys/class/net"
    try:
        names = []
        for name in sorted(os.listdir(base)):
            if name == "lo":
                continue
            names.append(name)
        return names
    except Exception:
        return []


def _run_command(command):
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr if stderr else stdout
        if not details:
            details = "Unknown error"
        return False, details
    return True, ""


def _apply_with_helper(enabled, incoming_policy, outgoing_policy, rule_arg_sets):
    helper_path = _resolve_helper_path()
    if not helper_path:
        return False, "Helper script not found: /usr/libexec/goldendog-firewall/ufw-apply"

    enabled_val = "on" if enabled else "off"
    incoming_val = "allow" if incoming_policy == "allow" else "deny"
    outgoing_val = "allow" if outgoing_policy == "allow" else "deny"

    rules_file = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            rules_file = tmp.name
            for arg_set in rule_arg_sets:
                tmp.write("\t".join(arg_set))
                tmp.write("\n")

        cmd = ["pkexec", helper_path, enabled_val, incoming_val, outgoing_val, rules_file]
        ok, error = _run_command(cmd)
        if not ok:
            return False, error
        return True, "Applied firewall settings with helper."
    finally:
        if rules_file and os.path.exists(rules_file):
            try:
                os.unlink(rules_file)
            except Exception:
                pass


def apply_firewall_configuration(enabled, incoming_policy, outgoing_policy, rule_arg_sets):
    """
    Apply firewall defaults and the listed ufw rules.
    rule_arg_sets must be a list of argument lists (without the ufw binary).
    """
    if os.geteuid() != 0:
        return _apply_with_helper(enabled, incoming_policy, outgoing_policy, rule_arg_sets)

    ufw_bin = _resolve_ufw_bin()
    commands = [
        [ufw_bin, "default", incoming_policy, "incoming"],
        [ufw_bin, "default", outgoing_policy, "outgoing"],
    ]

    for arg_set in rule_arg_sets:
        commands.append([ufw_bin] + arg_set)

    commands.append([ufw_bin, "--force", "enable"] if enabled else [ufw_bin, "--force", "disable"])

    for cmd in commands:
        ok, error = _run_command(cmd)
        if not ok:
            return False, f"{' '.join(cmd)}\n{error}"

    return True, f"Applied {len(commands)} firewall command(s)."
