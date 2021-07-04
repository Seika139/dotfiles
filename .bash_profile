# added by Anaconda3 4.3.1 installer
export PATH="$HOME/anaconda/bin:$PATH"

# Setting PATH for Python 3.6
# The original version is saved in .bash_profile.pysave
PATH="/Library/Frameworks/Python.framework/Versions/3.6/bin:${PATH}"
export PATH
eval "$(rbenv init -)"

# MacPorts Installer addition on 2017-11-06_at_23:05:02: adding an appropriate PATH variable for use with MacPorts.
export PATH="/opt/local/bin:/opt/local/sbin:$PATH"
# Finished adapting your PATH environment variable for use with MacPorts.

eval "$(rbenv init -)"
export PATH=~/bin:$PATH
eval "$(rbenv init -)"
export PATH="$HOME/.rbenv/bin:$PATH"

# ここから下は自分で書き足した(2019/4/21)
# 参考 : https://qiita.com/NorsteinBekkler/items/a0622ee6a39d08d61b72

# ここから下は自分で書き足した(2019/4/8)
# 参考 : https://qiita.com/hmmrjn/items/60d2a64c9e5bf7c0fe60
# 参考 : http://smootech.hatenablog.com/entry/2017/02/23/102531

if [ -f $(brew --prefix)/etc/bash_completion ]; then
    . $(brew --prefix)/etc/bash_completion
fi

# show git branch
# https://github.com/git/git/blob/master/contrib/completion/git-prompt.sh
source ~/.git-prompt.sh

# Gitブランチの状況を*+%で表示
GIT_PS1_SHOWDIRTYSTATE=true
GIT_PS1_SHOWUNTRACKEDFILES=true
GIT_PS1_SHOWSTASHSTATE=true
GIT_PS1_SHOWUPSTREAM=auto

export PS1='\[\e[96;40m\]\t \W\[\e[0m\]\[\e[1;32m\] $(__git_ps1 "(%s)") \[\e[0m\] \$ '

# for MySQL
export PATH="/usr/local/opt/mysql@5.6/bin:$PATH"

# for Laravel
export PATH="~/.composer/vendor/bin:$PATH"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion

# .bashrc を読み込む
test -r ~/.bashrc && . ~/.bashrc
