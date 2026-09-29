# Galactic Space Reborn

## Full Changelog

![Version Badge](https://img.shields.io/badge/Version-1.0--beta.3-green)
![Update Badge](https://img.shields.io/badge/Update_Type-Beta-purple)

### 1.0-Beta.3 — Getting Control

> This beta for Release 1.0 includes the addition of experimental controller support, a crash handler and a retiring of `manifest.json` in favor of `assets.json`

### ADDED

- Added Experimental Controller Support

> **Developer's Note**: Controller support is highly experimental and currently does not work on menus properly if at all.

- Added a Crash Handler

> **Developer's Note**: This will only trigger if the game crashes, you can use the crash logs created in the `/logs/` folder to file bug reports and the logs will be created with the filename in this format: `crash-YYYY-MM-DD HH:MM:SS.log`

### CHANGED

- Seperated asset definitions from game `/manifest.json` into `/assets/assets.json`

### REMOVED

- Removed `/manifest.json` in favor of `/assets/assets.json`

> **Developer's Note**: This was to setup the framework to go ahead and remove the assets folder from this repo completely to be hosted on a seperate repo, this will be the final beta that includes an assets folder in the repo before I move it to another public repo, this is for organization and to have the project be able to be compiled into an executable

---

### REPO UPDATES

- Moved the Resource Pack Documentation to README.md

> **Developer's Note**: Resource Pack Documentation is still a work in progress and I am also working on updates to the resource pack API and soon you will be able to modify assets, music and sounds more with a `.gsasset` file!

- Moved the game updates section in README.nd to the top of READNE,nd
