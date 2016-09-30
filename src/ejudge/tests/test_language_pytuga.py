import pytest

from ejudge import functions
from ejudge.tests import abstract as base

sources = """
## ok
nome = leia_texto("name: ")
mostre("hello %s!" % nome)

## wrong
nome = leia_texto("name: ")
mostre(nome)

## syntax
a b

## error
1 / 0

## recursive
função f(x):
    return 1 if x <= 1 else x * f(x - 1)

mostre(f(5))
"""


@pytest.mark.pytuga
class TestPytugaSupport(base.TestLanguageSupport):
    base_lang = 'pytuga'
    source_all = sources

    def test_pytuga_keeps_a_clean_environment(self, src_ok):
        functions.run(src_ok, ['tuga'], lang='pytuga', sandbox=False)
        assert str(True) == 'True'
