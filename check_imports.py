import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

modules = [
    ('brain', 'route_command'),
    ('agents.system_agent', 'execute_system_command'),
    ('agents.web_agent', 'web_search'),
    ('agents.automation_agent', 'execute_automation'),
    ('agents.chat_agent', 'chat_response'),
    ('agents.live_agent', 'handle_live_query'),
    ('agents.builder_agent', 'build_website'),
    ('agents.heartbeat_agent', 'measure_heart_rate'),
    ('voice', 'speak_text'),
    ('agents.crew_agent', 'run_tech_digest_crew'),
    ('face_auth', 'run_face_auth'),
]

for mod, fn in modules:
    try:
        m = __import__(mod, fromlist=[fn])
        getattr(m, fn)
        print(f"OK: {mod}.{fn}")
    except Exception as e:
        print(f"ERROR: {mod}.{fn} => {e}")
