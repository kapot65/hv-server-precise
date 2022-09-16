from argparse import ArgumentParser

def parse_args(): 
    parser = ArgumentParser(description='Rsh detector server redirecter.')

    in_grp = parser.add_argument_group("Input")
    # in_grp.add_argument('lan10_bin', type=str,
    #                     help='path lan10-12pci-base')
    in_grp.add_argument('-t', '--timeout', type=int, default=300,
                        help='command execution timeout in seconds '
                        '(default - 300)')
    in_grp.add_argument('--host', default='localhost',
                        help='server host (default - localhost)')
    in_grp.add_argument('-p', '--port', type=int, default=5555,
                        help='server port (default - 5555)')
    
    out_grp = parser.add_argument_group("Output")
    out_grp.add_argument('-o', '--out-dir', type=str, default="points",
                    help='output directory (default - "points")')
    out_grp.add_argument('--work-port', type=int, default=5555,
                        help='programm working port (default 5555)')
    
    acq_grp = parser.add_argument_group("Acquisition")
    def_rsh_path = "configs/rsh_conf.json"
    acq_grp.add_argument('-s', '--rsb-conf', type=str, default=def_rsh_path,
                        help='default rsb conf file pattern (default '
                             '%s)'%(def_rsh_path))
    acq_grp.add_argument('-z', '--zero-suppr', action="store_true",
                        help='use zero suppression on acquired data')
    acq_grp.add_argument('--zero-thresh', type=int, default=700,
                        help='zero suppression threshold in bins '
                        '(default - 500)')
    acq_grp.add_argument('--zero-area-l', type=int, default=50,
                        help='left neighborhood area size (in bins) which will'
                        ' be  saved during zero suppression'
                        '(default - 50)')
    acq_grp.add_argument('--zero-area-r', type=int, default=100,
                        help='left neighborhood area size (in bins) which will'
                        ' be  saved during zero suppression'
                        '(default - 100)')
    
    parser.add_argument('-l', '--logfile', default="rsh_server.log",
                        help='log filepath')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true", default=True)
    
    test_grp = parser.add_argument_group("Test")
    test_grp.add_argument('--test', action="store_true",
                        help='use default rsb file instead of acquisition')

    return parser.parse_args()