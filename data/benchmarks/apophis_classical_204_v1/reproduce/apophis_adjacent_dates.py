import concurrent.futures,subprocess,sys
dates=['2029-06-15T00:00:00','2029-07-15T00:00:00','2029-08-01T00:00:00']
def run(date):
    folder='runs/apophis_classical_204/chain_'+date[:10]
    try:
        done=subprocess.run([sys.executable,'runs/apophis_classical_chain.py',date,folder],timeout=1800)
        if done.returncode==0:subprocess.run([sys.executable,'runs/apophis_chain_accept.py',folder],timeout=180,check=True)
    except Exception as exc:print(date,repr(exc),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,dates))
