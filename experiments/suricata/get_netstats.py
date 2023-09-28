import os
import sys

def main():

    IP = '155.54.205.149'
    USER = 'quico'
    RUTA = '/home/quico/benchmarks/experiments/suricata'
    ARCHIVO = 'bigFlows.pcap'

    src_nic = 'enp5s0f1'
    dst_nic = 'enp1s0f0'
    replay_speed = 32
    nworkers = [1, 2, 4, 8, 16, 32, 64, 128]
        

    for i in range(len(sys.argv)):
        n = 2**i
        ID = sys.argv[i + 1]
        src_path = f"{RUTA}/logs,bm,{ID},{ARCHIVO},{n},{src_nic},{dst_nic},1,5,{replay_speed}/netstat.tcpreplay.{src_nic}.csv"
        dst_path = f"./logs,bm,{ID},{ARCHIVO},{n},{src_nic},{dst_nic},1,5,{replay_speed}"
        os.system(f"scp {USER}@{IP}:{src_path} {dst_path}")
    




if __name__ == "__main__":
    main()
