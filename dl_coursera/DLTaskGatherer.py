import os
import zipfile
import io
import logging
import re

from .lib.ExploringTree import ExploringTree

from .markup import render_supplement

from .resource import load_resource
from .define import *


def _sanitize_filename(s):
    return re.sub(r'[<>:"/\\|?*]', '_', s)


def _normalize_subtitle_lang(lang):
    return lang.strip().lower().replace('_', '-')


class DLTaskGatherer:
    def __init__(self, *, soc, outdir, subtitle_langs=None, transcript_langs=None, no_video=False):
        # "soc" means "sepc or course"
        assert soc['type'] in ['Spec', 'Course']

        self._soc = soc
        self._outdir = outdir
        self._subtitle_langs = subtitle_langs
        self._transcript_langs = transcript_langs
        self._no_video = no_video

        self._et = ExploringTree()
        self._resource_node = self._et.see('%s/resource' % self._soc['slug'])

        self._dl_tasks = []
        self._file_tasks = []
        self._playlist_entries = []
        self._used_filenames = set()

    def gather(self):
        (self._gather_spec if self._soc['type'] == 'Spec' else self._gather_course)(
            self._soc
        )

        _dir = self._path(self._resource_node.abspath()[1:])
        if not os.path.exists(_dir):
            with zipfile.ZipFile(io.BytesIO(load_resource('bundle.zip'))) as zf:
                zf.extractall(_dir)
            logging.info('new directory tree: %s' % _dir)

        for _ in self._file_tasks:
            data = _['data']
            filename = _['filename']
            if not os.path.exists(filename):
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'wb') as ofs:
                    ofs.write(data)
                logging.info('new file: %s' % filename)

        return self._dl_tasks

    def _resource_path(self):
        return self._et.relpathTo(self._resource_node)

    def _path(self, s):
        return os.path.abspath(os.path.join(self._outdir, s))

    def _add_dl_task(self, url, s):
        self._dl_tasks.append({'url': url, 'filename': self._path(s)})

    def _add_file_task(self, data, s):
        self._file_tasks.append({'data': data, 'filename': self._path(s)})

    def _down(self, s, i=None):
        if i is None:
            self._et.down(s)
        else:
            self._et.down('%02d - %s' % (i + 1, s))

    def _see(self, s):
        return self._et.see(s).abspath()[1:]

    def _see_at(self, relpath, filename):
        """See a file at a specific relative path from current position.
        Used to place files at module level regardless of current tree position."""
        return self._et.see(os.path.join(relpath, filename)).abspath()[1:]

    def _unique_filename(self, filename):
        # Track full paths for deduplication within the same directory
        # Since all files are now at module level, basenames are sufficient
        # but we use a module-scoped approach via the passed module_node
        if filename not in self._used_filenames:
            self._used_filenames.add(filename)
            return filename
        base, ext = os.path.splitext(filename)
        suffix = 1
        while True:
            candidate = '%s-%d%s' % (base, suffix, ext)
            if candidate not in self._used_filenames:
                self._used_filenames.add(candidate)
                return candidate
            suffix += 1

    def _gather_spec(self, spec):
        with self._et:
            self._down(spec['slug'])

            for _i, course in enumerate(spec['courses']):
                self._gather_course(course, _i)

    def _gather_course(self, course, i=None):
        with self._et:
            self._down(course['slug'], i)

            self._gather_course_references(course)

            for _i, module in enumerate(course['modules']):
                self._playlist_entries = []
                self._used_filenames = set()
                self._gather_module(module, _i)

    def _gather_course_references(self, course):
        with self._et:
            self._down('references')

            refid2node = {}
            for i, ref in enumerate(course['references']):
                item = ref['item']
                if item['type'] == 'CML':
                    refid2node[ref['id']] = self._et.see(
                        '%02d - %s.html' % (i + 1, _sanitize_filename(ref['name']))
                    )

            def fn_a(a):
                _refid = a.get('refid')
                if not _refid:
                    return

                _node = refid2node.get(_refid)
                if not _node:
                    logging.warning(
                        '[fn_a] unknown _refid=%s\n%s'
                        % (_refid, {_1: _2.abspath() for _1, _2 in refid2node.items()})
                    )
                else:
                    a['href'] = self._et.relpathTo(_node)

            self._fn_a = fn_a

            for i, ref in enumerate(course['references']):
                item = ref['item']
                if item['type'] == 'CML':
                    self._gather_cml_for_reference(item, i, ref)

    def _gather_module(self, module, i):
        with self._et:
            self._down(_sanitize_filename(module['name']), i)
            # Capture module node so all files are saved at module level
            module_node = self._et.whereami()

            for _i, lesson in enumerate(module['lessons']):
                self._gather_lesson(lesson, _i, module_node)

            # Generate playlist at module level
            self._gather_playlist(module_node)

    def _gather_lesson(self, lesson, i, module_node):
        # Don't navigate into lesson subfolder - all files go to module level
        # Prefix filenames with lesson index for uniqueness
        lesson_prefix = '%02d - %s' % (i + 1, _sanitize_filename(lesson['name']))

        for _i, item in enumerate(lesson['items']):
            if item['type'] == 'Lecture':
                self._gather_lecture(item, _i, lesson_prefix, module_node)
            elif item['type'] == 'Supplement':
                self._gather_supplement(item, _i, lesson_prefix, module_node)
            elif item['type'] == 'Quiz':
                self._gather_quiz(item, _i, lesson_prefix, module_node)

    def _gather_lecture(self, lecture, i, lesson_prefix, module_node):
        lecture_name = '%02d - %s' % (i + 1, _sanitize_filename(lecture['name']))
        # Prefix with lesson context for uniqueness when flattened
        full_lecture_name = '%s - %s' % (lesson_prefix, lecture_name)
        for _i, video in enumerate(lecture['videos']):
            self._gather_video(video, _i, full_lecture_name, module_node)

        for asset in lecture['assets']:
            self._gather_asset(asset, lesson_prefix, module_node)

    def _gather_video(self, video, i, title=None, module_node=None):
        # Use title (lecture name) for descriptive filenames at module level
        lecture_label = title if title else '%02d' % (i + 1)

        if not self._no_video:
            video_filename = '%s.mp4' % lecture_label
            video_filename = self._unique_filename(video_filename)
            # Save at module level using module_node reference
            video_rel = self._et.relpathTo(module_node)
            video_node = self._et.see(os.path.join(video_rel, video_filename))
            self._add_dl_task(video['url_video'], video_node.abspath()[1:])
            self._playlist_entries.append((video_node, title))

        subtitles = video.get('subtitles')
        if not subtitles and video.get('url_subtitle') is not None:
            subtitles = {'en': video['url_subtitle']}

        transcripts = video.get('transcripts') or {}

        # Build normalized lookup for transcripts
        transcript_lookup = {}
        for tlang, turl in transcripts.items():
            key = _normalize_subtitle_lang(tlang)
            transcript_lookup[key] = (tlang, turl)

        # Determine which languages need subtitles and which need transcripts
        selected_subtitles = self._select_subtitles(subtitles or {})
        selected_transcripts = self._select_transcripts(transcript_lookup)

        # Build sets of normalized language keys for each type
        subtitle_keys = set()
        for lang, url in selected_subtitles:
            subtitle_keys.add(_normalize_subtitle_lang(lang))

        transcript_keys = set()
        for lang, url in selected_transcripts:
            transcript_keys.add(_normalize_subtitle_lang(lang))

        # All languages involved in subtitle or transcript downloads
        all_keys = subtitle_keys | transcript_keys
        multi_lang = len(all_keys) > 1

        # Download subtitles (.srt) at module level
        for lang, url in selected_subtitles:
            key = _normalize_subtitle_lang(lang)
            has_both = key in transcript_keys
            if multi_lang or has_both:
                filename = '%s.%s.srt' % (lecture_label, lang)
            else:
                filename = '%s.srt' % lecture_label
            filename = self._unique_filename(filename)
            # Save at module level
            video_rel = self._et.relpathTo(module_node)
            self._add_dl_task(url, self._see_at(video_rel, filename))

        # Download transcripts (.txt) at module level
        for lang, url in selected_transcripts:
            key = _normalize_subtitle_lang(lang)
            has_both = key in subtitle_keys
            if multi_lang or has_both:
                filename = '%s - transcript.%s.txt' % (lecture_label, lang)
            else:
                filename = '%s - transcript.txt' % lecture_label
            filename = self._unique_filename(filename)
            # Save at module level
            video_rel = self._et.relpathTo(module_node)
            self._add_dl_task(url, self._see_at(video_rel, filename))

    def _select_transcripts(self, transcript_lookup):
        """Select transcript languages based on _transcript_langs, similar to _select_subtitles.

        When _transcript_langs is None (default), automatically select a transcript:
        prefer 'en' if available, otherwise select the only transcript if there's just one.
        """
        if not transcript_lookup:
            return []

        # Default behavior: select a transcript even when --transcripts is not specified
        if self._transcript_langs is None:
            if len(transcript_lookup) == 1:
                return [list(transcript_lookup.values())[0]]
            if 'en' in transcript_lookup:
                return [transcript_lookup['en']]
            return []

        selected = []
        seen = set()
        for lang in self._transcript_langs:
            key = _normalize_subtitle_lang(lang)
            if key in transcript_lookup and key not in seen:
                selected.append(transcript_lookup[key])
                seen.add(key)

        return selected

    def _gather_playlist(self, module_node):
        if not self._playlist_entries:
            return

        lines = ['#EXTM3U']
        for node, title in self._playlist_entries:
            if title:
                title = ' '.join(str(title).split())
                lines.append('#EXTINF:-1,%s' % title)
            lines.append(self._et.relpathTo(node))

        data = ('\n'.join(lines) + '\n').encode('UTF-8')
        # Save playlist at module level
        playlist_rel = self._et.relpathTo(module_node)
        self._add_file_task(data, self._see_at(playlist_rel, 'playlist.m3u'))

    def _select_subtitles(self, subtitles):
        if not subtitles:
            return []

        if self._subtitle_langs is None:
            if len(subtitles) == 1:
                return list(subtitles.items())
            if 'en' in subtitles:
                return [('en', subtitles['en'])]
            return []

        available = {}
        for lang, url in subtitles.items():
            key = _normalize_subtitle_lang(lang)
            available.setdefault(key, (lang, url))

        selected = []
        seen = set()
        for lang in self._subtitle_langs:
            key = _normalize_subtitle_lang(lang)
            if key in available and key not in seen:
                selected.append(available[key])
                seen.add(key)

        return selected

    def _gather_supplement(self, supplement, i, lesson_prefix, module_node):
        for _i, item in enumerate(supplement['items']):
            if item['type'] == 'CML':
                self._gather_cml(item, _i, supplement, lesson_prefix, module_node)

    def _gather_quiz(self, quiz, i, lesson_prefix, module_node):
        self._gather_supplement(quiz, i, lesson_prefix, module_node)

    def _gather_cml(self, cml, i, supplement, lesson_prefix, module_node):
        import bs4

        html = cml['html']
        html = bs4.BeautifulSoup(html, 'html.parser')
        for a in html.find_all('a'):
            self._fn_a(a)
        html = str(html)

        data = render_supplement(
            content=html,
            resource_path=self._resource_path(),
            title='%s' % supplement['name'],
        ).encode('UTF-8')
        # Prefix with lesson context and save at module level
        html_name = '%02d - %s.html' % (i + 1, _sanitize_filename(supplement['name']))
        html_name = self._unique_filename(html_name)
        cml_rel = self._et.relpathTo(module_node)
        self._add_file_task(data, self._see_at(cml_rel, html_name))

        for asset in cml['assets']:
            self._gather_asset(asset, lesson_prefix, module_node)

    def _gather_cml_for_reference(self, cml, i, ref):
        """Gather CML for course-level references, saved at course/references level."""
        import bs4

        html = cml['html']
        html = bs4.BeautifulSoup(html, 'html.parser')
        for a in html.find_all('a'):
            self._fn_a(a)
        html = str(html)

        data = render_supplement(
            content=html,
            resource_path=self._resource_path(),
            title='%s' % ref['name'],
        ).encode('UTF-8')
        self._add_file_task(
            data, self._see('%02d - %s.html' % (i + 1, _sanitize_filename(ref['name'])))
        )

        for asset in cml['assets']:
            self._add_dl_task(asset['url'], self._see(_sanitize_filename(asset['name'])))

    def _gather_asset(self, asset, lesson_prefix, module_node):
        name = asset['name']
        if name.lower().endswith('.pdf'):
            name = _sanitize_filename(lesson_prefix) + '.pdf'
        name = self._unique_filename(_sanitize_filename(name))
        asset_rel = self._et.relpathTo(module_node)
        self._add_dl_task(asset['url'], self._see_at(asset_rel, name))
