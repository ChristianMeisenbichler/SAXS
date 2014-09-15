gh-pages::
	cp -r doc/_build/html/* .
	git add *.html *.svg
	git add _images
	git commit -a
	git push origin gh-pages
