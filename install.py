import urllib2
import os
import sys
import subprocess
from subprocess import Popen, PIPE, STDOUT
import time
from optparse import OptionParser



# http://bacula.nti.tul.cz/~jan.brezina/flow123d_packages/1.8.0_master/flow123d_1.8.0_master_windows_x86_32.exe
url = "http://bacula.nti.tul.cz/~jan.brezina/flow123d_packages/1.8.0_master/flow123d_1.8.0_master_windows_x86_"


def downloadFile (url, save_as="installer.exe") :
    # get filename and prepare location
    file_name = url.split ('/')[-1]
    location = os.path.abspath (save_as)
    dirs = os.path.split (location)[0]

    if not os.path.exists (dirs) :
        os.makedirs (dirs)

    connection = urllib2.urlopen (url)
    handler = open (location, 'wb')
    meta = connection.info ()
    file_size = int (meta.getheaders ("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    percent = 0
    percent_new = 0
    while True :
        buffer = connection.read (block_sz)
        if not buffer :
            break

        file_size_dl += len (buffer)
        handler.write (buffer)
        percent_new = file_size_dl * 100. / file_size
        if percent_new > (percent + 15) or percent_new == 100 :
            status = r"%10d  [%3.2f%%]" % (file_size_dl, percent_new)
            status = status + chr (8) * (len (status) + 1)
            print status,
            percent = percent_new

    handler.close ()
    return location


def runMacro (filename, delay=0.5, timescale=1) :
    time.sleep (delay * timescale)
    subprocess.call (["c:\\Program Files (x86)\\AutoHotkey\\AutoHotkey.exe", "./commands/" + filename])


# subprocess.call(["flow123d"])

def writeToFile (filename, content) :
    f = open (filename, 'w')
    f.write (content if content is not None else ' ')
    f.close ()


def printParserError (parser, message) :
    print message
    parser.print_help ()
    sys.exit (1)


def silentInstall (installer_path, installation_path) :
    print "$> %s %s %s %s" % (uninstaller_path, "/S", "/NCRC", "/D=" + installation_path)
    subprocess.call ([installer_path, "/S", "/NCRC", "/D=" + installation_path])
    # some time to recover
    time.sleep (5)


def macroInstall (installer_path, installation_path) :
    p = Popen ([installer_path], stdout=PIPE, stdin=PIPE, stderr=PIPE)

    # welcome screen
    runMacro ("enter.ahk", 0.5)

    # license
    runMacro ("enter.ahk", 0.5)

    # path option
    runMacro ("down.ahk", 0.5)
    runMacro ("enter.ahk", 0.5)

    # target folder
    runMacro (macro_path, 0.5)

    # shortcut option
    runMacro ("enter.ahk", 0.5)

    # === INSTALLING === #

    # confirm after installation
    runMacro ("enter.ahk", 10)


def macroUninstall (uninstaller_path) :
    # welcome screen
    runMacro ("enter.ahk", 0.5)

    # === UNINSTALLING === #

    # confirm uninstallation
    runMacro ("enter.ahk", 10)


def silentUninstall (uninstaller_path) :
    print "$> %s %s" % (uninstaller_path, "/S")
    subprocess.call ([uninstaller_path, "/S"])
    # some time to recover
    time.sleep (5)


def runProgram (filename) :
    print "$> %s" % filename
    out, err = Popen ([filename], stdout=PIPE).communicate ()
    print out, err
    writeToFile ('output.log', out)
    writeToFile ('error.log', err)
    return (out, err)


if __name__ == "__main__" :

    parser = OptionParser ()
    parser.add_option ("-m", "--mode", dest="mode",
                       help="Specify value 'install' or 'uninstall' or 'run-outside' or 'run-inside'")
    parser.add_option ("-a", "--arch", dest="arch",
                       help="Specify value '32' or '64' for desired architecture type")
    parser.add_option ("-u", "--url", dest="url",
                       help="Optional url for downloading packgage")
    parser.add_option ("-i", "--not-silent", action="store_false", dest="silent", default=True,
                       help="Perform non silent GUI installation instead of silent command line installation")
    (options, args) = parser.parse_args ()

    sys.path.append ('c:/package_tests/cygwin64/bin/')
    sys.path.append ('c:/package_tests/cygwin32/bin/')
    print sys.path

    # args check
    if options.mode is None and options.arch is None :
        printParserError (parser, 'Arguments not specified!')
    if options.mode is None :
        printParserError (parser, 'Mode not specified!')
    if options.arch is None :
        printParserError (parser, 'Architecture not specified!')

    # mode check
    if str (options.mode) in ('install', 'uninstall', 'run_inside', 'run_outside') :
        perform_install = options.mode == "install"
        perform_uninstall = options.mode == "uninstall"
        perform_run_in = options.mode == "run_inside"
        perform_run_out = options.mode == "run_outside"
    else :
        printParserError (parser, "Unsupported mode '%s'" % str (options.arch))
        sys.exit (0)

    # architecture check and paths
    if str (options.arch) in ('32', '64') :
        installation_path = "c:\\package_tests\\cygwin" + str (options.arch) + "\\"
        installer_path = os.path.abspath ("Installer_" + str (options.arch) + ".exe")
        uninstaller_path = os.path.abspath (os.path.join (installation_path, "Uninstall.exe"))
        macro_path = "path" + str (options.arch) + ".ahk"
        arch = int (options.arch)
    else :
        printParserError (parser, "Unsupported architecture '%s'" % str (options.arch))
        sys.exit (0)

    # fix url
    if options.url is not None :
        url = options.url
    else :
        url = url + str (arch) + ".exe"

    if perform_install :
        print "DOWNLOADING"
        print url
        try :
            downloadFile (url, save_as=installer_path)
            print "\n Downloaded"
        except urllib2.HTTPError as err :
            print 'Cannot download file %s' % url
            print err
            sys.exit (1)

    if perform_install :
        print "INSTALLING"

        if options.silent :
            print "Silent installation..."
            silentInstall (installer_path, installation_path)
        else :
            print "Macro installation..."
            macroInstall (installer_path, installation_path)

        print "Installation complete"

        if os.path.isdir (installation_path) and os.path.exists (installation_path) :
            print "Installation successful"
        else :
            print "Installation FAILED"
            sys.exit (1)

    if perform_run_in or perform_run_out :
        print "RUNNING"
        bin = os.path.join (installation_path, "bin", "flow123d.exe")
        filename = bin if perform_run_in else "flow123dd"
        out, err = runProgram (filename)

        if str (out).find ("This is Flow123d, version") is -1 :
            print "Output failed"
            sys.exit (1)

        if err is not None :
            print "Error output failed"
            sys.exit (1)

    if perform_uninstall :
        print "UNINSTALLING"

        if options.silent :
            print "Silent uninstall..."
            silentUninstall (uninstaller_path)
        else :
            print "Macro uninstall..."
            macroUninstall (uninstaller_path)

        # deleting installer
        os.remove (installer_path)

        print "uninstallation complete"
        if not os.path.exists (installation_path) :
            print "Uninstallation successful"
        else :
            print "Uninstallation FAILED"
            sys.exit (1)

    sys.exit (0)















