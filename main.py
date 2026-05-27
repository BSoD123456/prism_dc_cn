#! python3
# coding: utf-8

from maker import make_maker

ROM_SRC = 'Prismaticallization (Japan).gdi'
ROM_OUT = 'Prismaticallization (ZH).gdi'

PATH_SRC = r'L:\Resource\Games\emu\dc\roms\Prismaticallization (Japan)\GDI'
PATH_OUT = r'L:\Resource\Games\emu\dc\roms\Prismaticallization (Japan)\OUTPUT'

PATHS = {
    'source': PATH_SRC,
    'output': PATH_OUT,
    'work': r'wktab\work',
    'extract': r'wktab\extract',
    'data': r'wktab\extract\data',
    'srcbak': r'wktab\srcbak',
}

if __name__ == '__main__':

    def main():
        mkr = make_maker(PATHS, ROM_SRC, ROM_OUT)
        mkr.make('all')

    try:
        main()
    except Exception as ex:
        print(ex)
        input('error')
