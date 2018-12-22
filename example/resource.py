from dl_coursera.resource import load_resource


def main():
    print(load_resource('__init__.py').decode('UTF-8'))


if __name__ == '__main__':
    main()
