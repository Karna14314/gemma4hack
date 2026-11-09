You fix one issue in the repository at /workspace with the smallest source change.
Hidden tests are applied to your git diff afterwards. An empty diff scores zero.

Budget: 28 tool calls, 8 minutes. When either runs out, the working tree is graded as it is.

1. Before any tool call, list the exact names, messages, status codes and return values the issue requires. Use them character for character.
2. Locate with one `git grep -n "<most specific string>" -- '*.py' | head -20`, then read at most 120 lines around the hit.
3. By your 12th tool call a source file must be edited. If unsure, edit the most likely function now.
4. Run at most one focused check (`pytest path::test -q` or `python -c ...`). Never run bare `pytest`.
   Fix only assertion failures about your change. Ignore fixture, import or pre-existing failures.
5. Scratch files go in /tmp. Never create or edit tests, conftest.py or pytest.ini.
6. Run `git diff`, revert any test path with `git checkout --`, then call submit_patch once.
