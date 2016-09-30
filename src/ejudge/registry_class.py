import importlib
import os

from ejudge.build_manager import BuildManager


class LanguageRegistry:
    """
    Registry that maps languages to managers.
    """

    def __init__(self):
        self._extensions = {}
        self._execution_managers = {}
        self._build_managers = {}

    def _register_extension(self, ext, language, force=False):
        """
        Register extension to the given language.
        """

        if ext.startswith('.'):
            ext = ext[1:]

        extensions = self._extensions
        if force and ext in extensions and ext != extensions[language]:
            raise RuntimeError(
                'extension %r is already registered to .%r' % (ext, language)
            )
        extensions[ext] = language

    def register(self, language, build, execution,
                 force=False,
                 extensions=(),
                 aliases=()):
        """
        Register execution/build manager classes for language.
        """

        for ext in extensions:
            self._register_extension(ext, language, force=force)

        self._execution_managers[language] = execution
        self._build_managers[language] = build
        for alias in aliases:
            self._execution_managers[alias] = execution
            self._build_managers[alias] = build

    def build_manager_class(self, language):
        """
        Return the BuildManager subclass associated with the given language.
        """

        manager_class = self._build_managers[language]
        if isinstance(manager_class, str):
            mod_name, _, manager_name = manager_class.rpartition('.')
            mod = importlib.import_module(mod_name)
            manager_class = getattr(mod, manager_name)
        return manager_class

    def build_manager(self, language, source, **kwargs):
        """
        Return a build manager instance for the given language string.

        It passes the source code instance and any other additional arguments
        passed to this function to the class constructor.
        """

        manager_class = self.build_manager_class(language)
        manager = manager_class(source, **kwargs)
        manager.language = language
        return manager

    def execution_manager(self, language, build_manager, inputs=(),
                          **kwargs):
        """
        Return an execution manager instance for the given language string.

        It passes the build_manager instance and any other additional arguments
        passed to this function to the class constructor.
        """

        assert isinstance(build_manager, BuildManager), build_manager
        manager_class = self.execution_manager_class(language)
        manager = manager_class(build_manager, inputs, **kwargs)
        manager.language = language
        return manager

    def execution_manager_class(self, language):
        """
        Return the execution manager class associated with the given language.
        """

        manager_class = self._execution_managers[language]

        if isinstance(manager_class, str):
            mod_name, _, manager_name = manager_class.rpartition('.')
            mod = importlib.import_module(mod_name)
            manager_class = getattr(mod, manager_name)

        return manager_class

    def language_from_extension(self, ext):
        """
        Return a language string from the given extension.
        """

        if ext.startswith('.'):
            ext = ext[1:]
        try:
            return self._extensions[ext]
        except KeyError:
            raise ValueError('unknown extension: %r' % ext)

    def language_from_filename(self, path):
        """
        Return the language string from a given filename.
        """

        ext = os.path.splitext(path)[1] or '.'
        return self.language_from_extension(ext)

    def language_from_source(self, file, path=None):
        """
        Return the language from either an explicit path or from a file object
        .name attribute.
        """

        return self.language_from_filename(getattr(file, 'name', path))

    def build_manager_from_path(self, lang, source, path, **kwargs):
        """
        Uses path information to load the most appropriate BuildManager.

        It accepts either a source string or a source file object.
        """

        if lang is None:
            lang = self.language_from_source(source, path)

        if not isinstance(source, str):
            source = source.read()

        return self.build_manager(lang, source, **kwargs)


registry = LanguageRegistry()
