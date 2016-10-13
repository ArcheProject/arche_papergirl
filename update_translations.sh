 #!/bin/bash
 #You need lingua and gettext installed to run this
 
 echo "Updating arche_papergirl.pot"
 pot-create -d arche_papergirl -o arche_papergirl/locale/arche_papergirl.pot arche_papergirl/.
 echo "Merging Swedish localisation"
 msgmerge --update  arche_papergirl/locale/sv/LC_MESSAGES/arche_papergirl.po  arche_papergirl/locale/arche_papergirl.pot
 echo "Updated locale files"
 
 