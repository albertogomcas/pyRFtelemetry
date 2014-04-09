# rFactor Remote LCD
# Copyright (C) 2014 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


sources = Glob("*.py", strings=True) + \
          Glob("rfactorlcd/*.py", strings=True)

flake_check = Command("flake.results", sources,
                      "python -m flake8.run --max-line-length=120 $SOURCES")

AlwaysBuild(Alias("test", [], "python -m unittest discover"))

for i in sources:
    Alias("pylint", Command(i + ".pylint", i, "/usr/bin/epylint $SOURCE"))

Default(flake_check)

Alias("all", [flake_check, "pylint", "test"])


# EOF #