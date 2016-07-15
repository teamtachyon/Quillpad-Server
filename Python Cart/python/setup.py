from distutils.core import setup, Extension
import os, os.path

QuillCCartModule = Extension(
        name = 'QuillCCart',
        sources = ['QuillCNCart.c', '../Cart.c'],
#         include_dirs = ['..'],
         libraries = ['expat'],
        include_dirs = [ os.path.split(os.getcwd())[0], os.path.expanduser('/usr/include/'), os.path.expanduser('/usr/local/include/python2.4/') ],
        )

setup ( name = 'QuillCCart',
        version = '1.0',
        description = 'Quill C Normal Cart package',
        ext_modules = [QuillCCartModule]
      )
