import pytest
import time

from ejudge import functions, registry
from iospec import parse as parse_string, datatypes, SimpleTestCase, \
    ErrorTestCase
from iospec.exceptions import BuildError


def source_property(name):
    @property
    def source_property(self):
        return self.get_source(name)
    return source_property


class TestLanguageSupport:
    base_iospec_source = (
        'name: <foo>\n'
        'hello foo!\n'
        '\n'
        'name: <bar>\n'
        'hello bar!'
    )
    base_lang = None
    source_all = None
    source_ok = source_property('ok')
    source_wrong = source_property('wrong')
    source_syntax = source_property('syntax')
    source_recursive = source_property('recursive')
    source_error = source_property('error')

    @pytest.fixture
    def iospec(self):
        return parse_string(self.base_iospec_source)

    @pytest.fixture
    def lang(self):
        return self.base_lang

    @pytest.fixture
    def src_ok(self):
        return self.source_ok

    @pytest.fixture
    def src_wrong(self):
        return self.source_wrong

    @pytest.fixture
    def src_syntax(self):
        return self.source_syntax

    @pytest.fixture
    def src_recursive(self):
        return self.source_recursive

    @pytest.fixture
    def src_error(self):
        return self.source_error

    @pytest.fixture
    def manager_cls(self, lang):
        return registry.build_manager_class(lang)

    @pytest.fixture
    def ex_manager_cls(self, lang):
        return registry.execution_manager_class(lang)

    @pytest.fixture(params=[True, False])
    def compare_streams(self, request):
        return request.param

    #
    # Auxiliary functions
    #
    @classmethod
    def get_source(cls, name):
        if cls.source_all is None:
            return None

        _, sep, data = cls.source_all.partition('## %s\n' % name)
        if not sep:
            return None
        data, _, _ = data.partition('\n## ')
        return data.strip()

    #
    # Test simple io.run() interactions
    #
    def test_run_valid_source(self, src_ok, lang, timeout=None, sandbox=False):
        tree = functions.run(src_ok, ['foo'], lang=lang, sandbox=sandbox,
                             timeout=timeout,
                             raises=True)
        try:
            assert len(tree) == 1
            case = tree[0]
            assert isinstance(case, SimpleTestCase)
            assert case[0] == 'name: '
            assert case[1] == 'foo'
            assert case[2] == 'hello foo!'
        except Exception:
            tree.pprint()
            raise

    def test_run_valid_source_with_timeout(self, src_ok, lang):
        self.test_run_valid_source(src_ok, lang, timeout=1.0)

    @pytest.mark.sandbox
    def test_run_valid_source_with_sandbox(self, src_ok, lang):
        self.test_run_valid_source(src_ok, lang, sandbox=True)

    @pytest.mark.sandbox
    def test_run_valid_source_with_sandbox_and_timeout(self, src_ok, lang):
        self.test_run_valid_source(src_ok, lang, sandbox=True, timeout=1.0)

    def test_run_source_with_runtime_error(self, src_error, lang):
        tree = functions.run(src_error, ['foo'], lang=lang, sandbox=False)
        tree.pprint()
        assert isinstance(tree[0], ErrorTestCase)
        assert tree[0].error_type == 'runtime'

    def test_run_from_input_sequence(self, src_ok, lang):
        inputs = [['foo'], ['bar']]
        tree = functions.run(src_ok, inputs, lang=lang, sandbox=False)
        assert len(tree) == 2
        assert tree[0][2] == 'hello foo!'
        assert tree[1][2] == 'hello bar!'

    def test_run_valid_source_from_iospec_input(self, src_ok, lang):
        case1 = datatypes.SimpleTestCase([datatypes.In('foo'), datatypes.Out('foo')])
        case2 = datatypes.InputTestCase([datatypes.In('bar')])
        inpt = datatypes.IoSpec([case1, case2])
        tree = functions.run(src_ok, inpt, lang=lang, sandbox=False)
        assert len(tree) == 2
        assert tree[0][2] == 'hello foo!'
        assert tree[1][2] == 'hello bar!'

    def test_run_code_with_syntax_error(self, src_syntax, lang):
        ast = functions.run(src_syntax, ['foo'], lang=lang, sandbox=False)
        assert len(ast) == 1
        assert isinstance(ast[0], datatypes.ErrorTestCase)
        assert ast[0].error_type == 'build'

    def test_run_recursive_function(self, src_recursive, lang):
        result = functions.run(src_recursive, [()], lang=lang, sandbox=False)
        result.pprint()
        assert list(result[0]) == ['120']

    @pytest.mark.sandbox
    def test_run_recursive_function_in_sandbox(self, src_recursive, lang):
        result = functions.run(src_recursive, [()], lang=lang, sandbox=True)
        result.pprint()
        assert list(result[0]) == ['120']

    def test_raises_timeout_error(self, lang, iospec, fake=False,
                                  sandbox=False):
        src = self.get_source('timeout')
        if src is None:
            return

        t0 = time.time()
        result = functions.run(src, iospec, lang=lang, timeout=0.1,
                               sandbox=fake or sandbox, fake_sandbox=fake,
                               debug=True)
        dt = time.time() - t0
        result.pprint()
        assert result.get_error_type() == 'timeout'
        assert dt < 1.5

    @pytest.mark.sandbox
    def test_raises_timeout_error_in_sandbox(self, lang, iospec, fake=False):
        self.test_raises_timeout_error(lang, iospec, fake)

    #
    # Test grading and check if the feedback is correct
    #
    def test_valid_source_receives_maximum_grade(self, iospec, src_ok, lang,
                                                 compare_streams):
        feedback = functions.grade(src_ok, iospec, lang=lang, sandbox=False,
                                   compare_streams=compare_streams)
        feedback.pprint()
        assert isinstance(feedback.answer_key, datatypes.TestCase)
        assert isinstance(feedback.testcase, datatypes.TestCase)
        assert feedback.grade == 1
        assert feedback.message is None
        assert feedback.status == 'ok'

    def test_wrong_source_receives_null_grade(self, iospec, src_wrong, lang,
                                              compare_streams):
        feedback = functions.grade(src_wrong, iospec, lang=lang, sandbox=False,
                                   compare_streams=compare_streams)
        assert feedback.grade == 0
        assert feedback.status == 'wrong-answer'
        assert feedback.title == 'Wrong Answer'

    #
    # Test build managers
    #
    def test_build_manager_has_the_correct_language(self, manager_cls, src_ok, lang):
        manager = manager_cls(src_ok)
        assert manager.language == lang

    def test_build_manager_can_build(self, manager_cls, src_ok):
        manager = manager_cls(src_ok)
        assert manager.is_built is False
        manager.build()
        assert manager.is_built is True

    def test_build_manager_raise_build_error(self, manager_cls, src_syntax):
        manager = manager_cls(src_syntax)
        with pytest.raises(BuildError):
            manager.build()

    def test_build_manager_can_build_in_sandbox(self, manager_cls, src_ok):
        manager = manager_cls(src_ok, is_sandboxed=True)
        assert manager.is_sandboxed
        assert manager.is_built is False
        manager.build()
        assert manager.is_built is True

    def test_build_manager_raise_build_error(self, manager_cls, src_syntax):
        manager = manager_cls(src_syntax)
        with pytest.raises(BuildError):
            manager.build()

    def test_build_manager_detect_syntax_error_before_build(self, manager_cls, src_syntax, src_ok):
        manager = manager_cls(src_ok)
        manager.syntax_check()  # nothing happens

        manager = manager_cls(src_syntax)
        with pytest.raises(SyntaxError):
            manager.syntax_check()
