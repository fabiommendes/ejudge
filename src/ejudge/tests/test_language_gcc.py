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
#include<stdio.h>

int main(void) {
    int x[1];
    printf("bad\n");
    printf("x: %d\n", x[1000]);
    return 1;
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


## timeout
#include<stdio.h>
#include<time.h>

int main(void) {
    clock_t t0 = clock();
    clock_t tf = t0 + 5 * CLOCKS_PER_SEC;

    while (clock() < CLOCKS_PER_SEC) {
        clock(); // procrastinate. We don't sleep as it seems to break boxed...
    }
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

    def test_run_with_compare_streams(self, src_ok):
        obj = functions.run(src_ok, ['john'], lang='c', compare_streams=True,
                            sandbox=False)
        case = obj[0]
        case.pprint()
        assert len(case) == 2
        assert case[0] == 'john'
        assert case[1] == 'name: hello john!'

    def test_run_bad_program_with_compare_streams(self, src_error):
        obj = functions.run(src_error, ['john'], lang='c', compare_streams=True,
                            sandbox=False)
        case = obj[0]
        case.pprint()
        assert len(case) == 2
        assert case.error_type == 'runtime'


@pytest.mark.c
@pytest.mark.gcc
def test_c_syntax_check_detect_invalid_syntax(compiler):
    good_src = TestGCCSupport.get_source('ok')
    bad_src = good_src + '\n}'

    assert c_syntax_check(good_src, compiler=compiler) is None
    with pytest.raises(SyntaxError):
        c_syntax_check(bad_src, compiler=compiler)
