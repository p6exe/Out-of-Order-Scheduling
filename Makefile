.PHONY: clean test

test: Project1.py test.in
	Python Project1.py < test.in > out.txt

clean:
	-rm out.txt
