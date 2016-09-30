import pytest

from ejudge import functions
from ejudge.langs.c_family import c_syntax_check
from ejudge.tests import abstract as base

sources = r"""
## ok
#include<stdio.h>

int main(void) {
    char buffer[100];
    printf("name: ");
    scanf("%s", buffer);
    printf("hello %s!\n", buffer);
}


## wrong
#include<stdio.h>

int main(void) {
    char buffer[100];
    puts("name: ");
    scanf("%s", buffer);
    printf("%s\n", buffer);
}


## syntax
a b

## error
int main(void) {
    char buffer[10];
    char c = buffer[1000];
}


## recursive
#include<stdio.h>

int f(int x) {
    return (x <= 1)? 1: x * f(x - 1);
}

int main(void) {
    printf("%d\n", f(5));
}


## twoinputs
#include<stdio.h>
void main() {
    char name[100], job[200];
    printf("name: ");
    scanf("%s", name);
    printf("job: ");
    scanf("%s", job);
    printf("%s, %s\n", name, job);
}

"""


@pytest.fixture(params=['clang', 'gcc', 'tcc'])
def compiler(request):
    return request.param


@pytest.mark.c
@pytest.mark.gcc
class TestGCCSupport(base.TestLanguageSupport):
    base_lang = 'c'
    source_all = sources

    @pytest.fixture
    def twoinputs(self):
        return self.get_source('twoinputs')

    def test_c_program_with_two_inputs(self, twoinputs):
        result = functions.run(twoinputs, ['foo', 'bar'], lang='c',
                               sandbox=False)
        case = result[0]
        print(result.to_json())
        result.pprint()
        assert list(case) == ['name: ', 'foo', 'job: ', 'bar', 'foo, bar']


@pytest.mark.c
@pytest.mark.gcc
def test_c_syntax_check_detect_invalid_syntax(compiler):
    good_src = TestGCCSupport.get_source('ok')
    bad_src = good_src + '\n}'

    assert c_syntax_check(good_src, compiler=compiler) is None
    with pytest.raises(SyntaxError):
        c_syntax_check(bad_src, compiler=compiler)
