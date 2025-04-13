example:
	@VAR=1
	@echo "$$VAR"

example2:
	# コメント
	@VAR=2; \
	echo "$$VAR"

MY_LOCAL_VAR := hello_from_make
export MY_ENV_VAR := hello_from_env

test:
	@echo "Local variable in make: $(MY_LOCAL_VAR)"
	@sh -c 'echo "Local variable in shell: $$MY_LOCAL_VAR"'
	@echo "Environment variable in make: $(MY_ENV_VAR)"
	@sh -c 'echo "Environment variable in shell: $$MY_ENV_VAR"'

$(warning MAKE = $(MAKE))  # => Makefile:18: MAKE = /Library/Developer/CommandLineTools/usr/bin/make
$(warning CC = $(CC)) # => Makefile:19: CC = gcc
$(warning CFLAGS = $(CFLAGS)) # => Makefile:20: CFLAGS =  -Wall -Wextra -Werror
