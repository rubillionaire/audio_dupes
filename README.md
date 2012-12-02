Move duplicate audio
====================

Moves duplicate MP3 and M4A files to another directory.

Note: This repo was originally setup to flag audio files with a bit of metadata. But iTunes choked on the library, so the approach has shifted to moving the files. Once moved, one can [manually clean up itunes][0]

### Setup.

	pip install -r reqs.txt
	
### Execute.

	python move_dupes.py /path/to/itunes/music/ /dupe/dir/
	
[0]: http://www.youtube.com/watch?v=nQ7SNNjd78Y