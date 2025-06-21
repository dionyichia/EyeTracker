# Developers Manual
Instructions for Debugging, Profiling, and Releasing.

## Profiling
To profile the software workload, from the project root directory run:

`python -m app.core.profiler`


## Releasing
To create a new release:
1. Save changes to git

`git add .`
`git commit -m "_your_commit_message"`

2. Test build locally
`python script/build.py`
- test the executable

3. Tag commit to version

4. Git push