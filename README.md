# btcrecover with my notes

## Introduction

btcRecover original [here](https://github.com/3rdIteration/btcrecover/archive/master.zip)
My copy here => [./btcrecover-original](./btcrecover-original)

## Installation troubleshooting

### Error with coincurve:

get btcRecover: 

`wget  https://github.com/3rdIteration/btcrecover/archive/master.zip`


Run: 

`sudo apt-get install -y python-dev build-essential procps curl file git autoconf autogen`

Edit requirements.txt and downgrade coincurve to 16.0.0

Run:

`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

`eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"`

`brew install gcc automake pkg-config libtool libffi gmp`

`pip3 install -r requirements.txt`

Run Tests: 

`python run-all-tests.py -vv`

### Error Updating Python3 pip AttributeError (OpenSSL_add_all_algorithms)

module 'lib' has no attribute 'OpenSSL_add_all_algorithms'
https://stackoverflow.com/questions/74981558/error-updating-python3-pip-attributeerror-module-lib-has-no-attribute-openss

Run: 

`sudo apt purge python3 python3-pip python3-openssl`

`rm -rf ~/.local/lib/python3.8`

`sudo apt install libssl-dev libffi-dev python3 python3-pip python3-openssl`

---

## btcRecover in action


### With partial seeds:

Command:

`python3 seedrecover.py --no-dupchecks --mnemonic-length 12 --language EN --dsw --wallet-type BIP39 --addr-limit 10 --addrs bc1q7kw2uepv6hfffhhxx2vplkkpcwsslcw9hsupc6 --tokenlist ./seed-list-all.txt`

Example from [here](https://btcrecover.readthedocs.io/en/latest/Usage_Examples/2022-04-02_Seed_Tokenlist_TokenBlocks/example_seed_tokenlist_tokenblocks/):

Command:

`python3 seedrecover.py --tokenlist ./seed-list-all-example.txt --mnemonic-length 24 --language en --wallet-type bip39 --addrs 1PTcESpqrmWePYB5h18Ni11QTKNfMkdSYJ --dsw --addr-limit 10 --max-tokens 9 --min-tokens 8`

Result:

`correct seeds: basic dawn renew punch arch situate resist indicate call lens group empty brother damp this verify eternal injury arrest question armor hole lounge practice`


### with 12 seeds:

`python3 seedrecover.py --no-dupchecks --mnemonic-length 12 --language EN --dsw --wallet-type BIP39 --addr-limit 1 --addrs bc1q7kw2uepv6hfffhhxx2vplkkpcwsslcw9hsupc6 --seedlist ./seed-list.txt`

seed-list.txt content (put in lower-case, upper-case and so on):
    ocean hidden kidney famous rich season gloom husband spring boy attitude convince
    ocean hidden kidney famous rich season gloom husband spring boy convince attitude
    ocean hidden kidney famous rich season gloom husband spring attitude boy convince

### To recover password: 
`python btcrecover.py --bip39 --addrs bc1q7kw2uepv6hfffhhxx2vplkkpcwsslcw9hsupc6 --addr-limit 10 --passwordlist ./password-list.txt --mnemonic "ocean hidden kidney famous rich season gloom husband spring boy attitude convince"`

### Other example commands:

`python seedrecover.py --wallet-type bip39 --addrs bc1qv87qf7prhjf2ld8vgm7l0mj59jggm6ae5jdkx2 --mnemonic "element entire sniff tired miracle solve shadow scatter hello never tank side sight isolate sister uniform advice pen praise soap lizard festival connect" --addr-limit 5`

`python seedrecover.py --wallet-type bip39 --addrs 3NiRFNztVLMZF21gx6eE1nL3Q57GMGuunG --mnemonic "element entire sniff tired miracle solve shadow scatter hello never tank side sight isolate sister uniform advice pen praise soap lizard festival connect" --addr-limit 5`

`python3 seedrecover.py --no-dupchecks --mnemonic-length 12 --language EN --dsw --wallet-type BIP39 --addr-limit 1 --addrs 17GR7xWtWrfYm6y3xoZy8cXioVqBbSYcpU --tokenlist ./btcrecover/test/test-listfiles/SeedTokenListTest.txt`

`python3 seedrecover.py --wallet-type bip39 --addrs 15p2ihGM9xonsR3Z4W7bqZxBSCyEvNoVz2 --mnemonic "change solution sail drama shadow situate stove protect reform pool neglect swamp" --addr-limit 5`

`python3 seedrecover.py --no-dupchecks --mnemonic-length 12 --language EN --dsw --wallet-type BIP39 --addr-limit 1 --addrs 17GR7xWtWrfYm6y3xoZy8cXioVqBbSYcpU --tokenlist ./btcrecover/test/test-listfiles/SeedTokenListTest.txt`


