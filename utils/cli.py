from argparse import ArgumentParser

def parse_args(): 
    parser = ArgumentParser(description='TODO: add desc')
    
    parser.add_argument('-l', '--logfile', default="hv_server.log",
                        help='log filepath')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true", default=True)

    return parser.parse_args()