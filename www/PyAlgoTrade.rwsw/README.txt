RapidWeaver Sandwich (.rwsw) README
===================================

This is a RapidWeaver Sandwich (.rwsw) file, which is designed to be a "bundle"
(directory) on Mac OS X.  If you are reading this, it's assumed that you're
somewhat curious about the innards of how RapidWeaver stores its data.  Feel
free to do this: the RapidWeaver file format is designed to be open and
hackable, and we welcome tools that can read our file format!  Here's what you
need to know about the RapidWeaver file format to play with it.

Note that this README.txt file is designed to give you the minimum amount of
information necessary to peek and poke around the .rwsw bundle.  For more
extensive information on the RapidWeaver Sandwich file format, please
visit the Realmac Software website at <http://www.realmacsoftware.com/>
and check out our developer documentation.

Sandwiches
----------

 * Every directory must have a Contents.plist file, which is an Apple
   Property List file; man plist(5) for more details.  A directory that has a
   Contents.plist file in it is called a "Sandwich".  All directories must
   be sandwiches, i.e. all directories _must_ have a Contents.plist file in
   them.  For robustness and interoperability reasons, most (or all) plist
   files you encounter will be stored as XML, but you may also encounter binary
   plist files for Contents.plist files that can become potentionally large
   sizes (100k+), and whose contents are not critical for your data integrity.

 * A sandwich's Contents.plist file has a dictionary for its Root property.
   This top-level dictionary has two keys: Type, which indicates the type of
   data this directory stores (e.g. "Page Attributes" or "Publishing
   Manifest"), and a second key named SandwichFillings.
   
Sandwich Fillings
-----------------

 * The SandwichFillings key in the Contents.plist dictionary is an array of
   dictionaries.  Each of these dictionaries is called a "Sandwich Filling",
   and the offset into the array reflects different versions.  As an example,
   an array of three dictionaries has three sandwich fillings: a version 0
   filling, version 1 filling, and a version 2 filling.
   
 * The array of sandwich filling versions is meant for easy forward and
   backward compatibility.  Backward compatibility is achieved by an
   application only reading sandwich fillings up to a particular version that
   it understands.  For example, RapidWeaver 4.0 may only understand version
   0 of a particular sandwich type, but RapidWeaver 4.1 may understand both
   version 0 and version 1.  (It is implicit that if an application understands
   version n, it will understand versions [0..n]).  Forward compatibilty is
   achieved by an application simply ignoring version numbers that it does not
   understand, and re-writing those sandwich filling versions out verbatim when
   it re-saves the file.
 
 * Each sandwich filling has three keys: Files (an array), Subsandwiches (also
   an array), and Dictionary (surprise surprise, a dictionary).

 * The Files key contain filenames in the current sandwich directory that
   are referenced by that version of the sandwich.  This enables version
   0 of a sandwich filling to reference OLDFILE.blob that may contain some
   data, and version 1 of a sandwich filling that references NEWFILE.blob,
   which contains additional information supplementing OLDFILE.blob.  Note
   that files referenced by the Files array are required to be regular
   files or directories, so no symbolic links (or special block
   devices...) are allowed to reside in a sandwich.
   
 * For performance reasons, referenced files usually share multiple hardlinks.
   (This applies to this README.txt file as well -- it is hardlinked to the
   Resources/Sandwich-README.txt in the RapidWeaver.app application bundle,
   and therefore has the same inode number.)  If you are editing files manually,
   make sure to check that the editor you are using saves to a different file
   inode, otherwise other Sandwich documents on the same volume will share the
   changes you've just made!  (For example, in Vim, make sure you do
   ":set backupcopy=breakhardlink".)
   
 * The Subsandwiches array refers to further sandwich directories inside this
   sandwich.

 * The Dictionary key contains an arbitrary key-value dictioanry that holds
   information too small to efficiently stored as separate files.  This is
   useful for storing short strings, numbers, and boolean values for the
   application.

Attributed String and Archive Files
-----------------------------------

 * Sandwiches may contain files with a .as extension.  This is a native Cocoa
   representation of the NSAttributedString class, serialised directly to disk
   via NSKeyedArchiver.  While the .rtf and .rtfd file formats are de-facto
   standards for storing NSAttributedStrings to disk in a directly editable
   fashion, those file formats do not store any custom attributes in the file
   format, which RapidWeaver uses extensively.  As such, .rtf and .rtfd files
   are lossy formats for RapidWeaver and cannot be used to store all data in
   a text field.  For best performance and data reliability, we chose to use
   Cocoa's native archiving mechanism to store attributed strings to disk.
   
 * We provide a command-line BSD tool in the RapidWeaver.app application bundle
   named "astool" that can manipulate attributed string files.  See the
   astool(1) manpage (in the Resources/ directory of the RapidWeaver.app
   bundle) for more information.  You are also welcome to write your own
   simple Cocoa programs to read and write .as files, of course: simply use
   +[NSKeyedUnarchiver unarchiveObjectWithFile:] to instantiate an
   NSAttributedString object from the file on disk.
   
 * Files with a .archive extension are similar to .as files in that they are
   direct Cocoa archives of objects, but may be an arbitrary class.  Manipulate
   them at your own risk.
   
 * It may be useful to know that Cocoa archives are stored as binary property
   list files; you can, in fact, rename the files to have a .plist extension
   and open the files up in Apple's standard Property List editor that comes
   bundled with the Xcode Tools.  Good luck trying to make sense of the
   archive, though :).

- Realmac Software <http://www.realmacsoftware.com/>

