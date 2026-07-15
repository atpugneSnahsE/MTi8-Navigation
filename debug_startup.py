import traceback

try:
    import main
    print('imported main')
    nav = main.NavigationSystem()
    print('initialized NavigationSystem')
except Exception as exc:
    print('STARTUP_ERROR', repr(exc))
    traceback.print_exc()
