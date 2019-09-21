from dl_coursera.lib.ExploringTree import ExploringTree


def main():
    et = ExploringTree()

    def jump(s):
        old = et.whereami()
        new = et.jump(s)
        print('%s -> %s' % (new.relpathFrom(old), new))

    print('whereami: %s\n' % et.whereami())

    with et:
        jump('quick')
        jump('.')
        jump('fox')
        jump('..')
        jump('/ali/ce/bo/b')
        jump('..////../')
        jump('/lazy/do/g')

    print('\nwhereami: %s' % et.whereami())


if __name__ == '__main__':
    main()
