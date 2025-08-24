#!/usr/bin/env python3

import argparse


def create_parser():
    parser = argparse.ArgumentParser(
        prog='rk800',
        description='RK800 CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='available commands')
    
    # configure
    configure_parser = subparsers.add_parser('configure', help='configure RK800')
    configure_parser.add_argument('arch', choices=['arm32', 'aarch64', 'linux'], help='target architecture')
    configure_parser.add_argument('project', choices=['loader', 'daemon'], help='project to configure')
    
    # listen
    listen_parser = subparsers.add_parser('listen', help='start listening')
    listen_parser.add_argument('listen_addr', help='address to bind to')
    listen_parser.add_argument('listen_port', type=int, help='port to listen on')
    
    return parser


def parse_args(args=None):
    parser = create_parser()
    return parser.parse_args(args)