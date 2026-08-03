@echo off
set GIT_DIR=%TEMP%\clipmind_git
set GIT_WORK_TREE=%~dp0
git --git-dir=%GIT_DIR% --work-tree=%GIT_WORK_TREE% %*
