import typer
import docker
from mdutils.mdutils import MdUtils
from mdutils import Html

import shutil
import json
import subprocess
from os import listdir, mkdir, makedirs, remove
from os.path import abspath, join, isfile, exists, dirname
from functools import reduce

SANDBOX_IMAGE_TAG = 'cs577_layrex:latest'
SANDBOX_CONTAINER_PREFIX = 'layrex_sandbox_'

app = typer.Typer()
dockerd = docker.from_env()


# returns (return_val, stdout, stderr)
def execute(cmd):
    process = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (process.returncode, process.stdout, process.stderr)


def collectApps(path):
    files = [f for f in listdir(path) if isfile(join(path, f))]
    return files


def cleanUp():
    containers = dockerd.containers.list()
    for container in containers:
        if SANDBOX_CONTAINER_PREFIX in container.name:
            container.kill()
            container.remove()
    networks = dockerd.networks.list()
    for network in networks:
        if SANDBOX_CONTAINER_PREFIX in network.name:
            network.remove()


def createNetwork(tag):
    network = dockerd.networks.create(
        tag, driver='bridge', internal=True, enable_ipv6=False)
    return 'br-' + network.id[0:12]


# def createNetwork(tag):
#     (exitcode, stdout, stderr) = execute(
#         ['docker', 'network', 'create', '-d', 'bridge', tag])
#     if stderr:
#         stderr = typer.style(stderr.decode('ascii'), fg=typer.colors.RED)
#         typer.echo('Failed create sandbox network:')
#         typer.echo(f'   tag:{tag}')
#         typer.echo(f'   stderr:\n{stderr}')
#         exit(1)
#     else:
#         net = 'br-' + str.strip(stdout.decode('ascii'))[0:12]
#         return net


def removeNetwork(tag):
    (exitcode, stdout, stderr) = execute(
        ['docker', 'network', 'rm', tag])
    if stderr:
        stderr = typer.style(stderr.decode('ascii'), fg=typer.colors.RED)
        typer.echo('Failed remove sandbox network:')
        typer.echo(f'   tag:{tag}')
        typer.echo(f'   stderr:\n{stderr}')
        exit(1)
    else:
        typer.echo('Removed sandbox network:')
        typer.echo(f'   tag:{tag}')


def startTcpdump(nicId, password=None):
    # command = ['tcpdump', '-i', 'ens4', '-w', '-']
    # if password:
    #     command = ['echo', password, '|', 'sudo', '-s'] + command
    process = subprocess.Popen(
        f'echo {password} | sudo -S tcpdump -i {nicId} -w - | tcpdump -r -',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)
    return process


def getRawTcpdump(process):
    # try:
    stdout, stderr = process.communicate()
    return {'exit': process.returncode,
            'stdout': stdout.decode('ascii'),
            'stderr': stderr.decode('ascii')}
    # except subprocess.TimeoutExpired:
    #     print('Failed to terminate subprocess')
    #     exit(1)


def getTcpdumpSummary(raw):
    pass


def startSandbox(tag, nicId):
    try:
        container = dockerd.containers.run(
            SANDBOX_IMAGE_TAG,
            stdin_open=True,
            name=tag,
            network=nicId,
            detach=True,
            remove=True)
        typer.echo('Started sandbox container.')
    except docker.errors.APIError:
        raise
    return container


# def startSandbox(tag):
    # execute(['docker', 'kill', tag])
    # (exitcode, stdout, stderr) = execute(
    #     ['docker', 'run', '-itd', '--rm', '--name', tag, SANDBOX_IMAGE_TAG])
    # if stderr:
    #     stderr = typer.style(stderr.decode('ascii'), fg=typer.colors.RED)
    #     typer.echo('Failed to start sandbox container:')
    #     typer.echo(f'   tag:{tag}')
    #     typer.echo(f'   stderr:\n{stderr}')
    #     exit(1)
    # else:
    #     chash = str.strip(stdout.decode('ascii'))
    #     typer.echo('Started sandbox container:')
    #     typer.echo(f'   tag: {tag}')
    #     typer.echo(f'   hash: {chash}')


def killSandbox(container):
    try:
        container.kill()
        # try:
        #     container.remove()
        # except docker.errors.APIError:
        #     pass
        typer.echo('Killed sandbox container.')
    except docker.errors.APIError:
        raise

# def stopSandbox(tag):
    # (exitcode, stdout, stderr) = execute(['docker', 'kill', tag])
    # if stderr:
    #     stderr = typer.style(stderr.decode('ascii'), fg=typer.colors.RED)
    #     typer.echo('Failed to kill sandbox container:')
    #     typer.echo(f'   tag:{tag}')
    #     typer.echo(f'   stderr:\n{stderr}')
    #     exit(1)
    # else:
    #     ctag = str.strip(stdout.decode('ascii'))
    #     typer.echo('Stopped sandbox container:')
    #     typer.echo(f'   tag: {ctag}')


def copyApp(tag, path):
    (exitcode, stdout, stderr) = execute(
        ['docker', 'cp', path, tag+':/root/app'])
    if stderr:
        stderr = typer.style(stderr.decode('ascii'), fg=typer.colors.RED)
        typer.echo('Failed to copy app:')
        typer.echo(f'   tag: {tag}')
        typer.echo(f'   stderr:\n{stderr}')
        exit(1)


# def execApp(container, stdin):
#     result = container.exec_run('./app', stderr=True, stdout=True, stdin=True)
#     # s = container.attach_socket(params={'stdin': 1, 'stream': 1}, ws=True)
#     s = result[1]
#     # s.send(stdin)
#     # s.close()
#     print(result)
#     return {'exit': result[0],
#             'stdout': s[0].decode('ascii'),
#             'stderr': s[1].decode('ascii')}

    # (exitcode, stdout, stderr) = execute(
    #     ['docker', 'exec', '-it', tag, './app'])
    # stdoutf = typer.style(stdout.decode('ascii'), fg=typer.colors.GREEN)
    # stderrf = typer.style(stderr.decode('ascii'), fg=typer.colors.RED)
    # typer.echo('Executing app:')
    # typer.echo(f'   container: {tag}')
    # typer.echo(f'   exitcode: {exitcode}')
    # typer.echo(f'   stdout: \n{stdoutf}')
    # typer.echo(f'   stderr:\n{stderrf}')
    # return {'exit': exitcode,
    #         'stdout': stdout.decode('ascii'),
    #         'stderr': stderr.decode('ascii')}


def execApp(tag):
    (exitcode, stdout, stderr) = execute(
        ['docker', 'exec', tag, './app'])
    stdoutf = typer.style(stdout.decode('ascii'), fg=typer.colors.GREEN)
    stderrf = typer.style(stderr.decode('ascii'), fg=typer.colors.RED)
    typer.echo('Executing app:')
    typer.echo(f'   container: {tag}')
    typer.echo(f'   exitcode: {exitcode}')
    typer.echo(f'   stdout: \n{stdoutf}')
    typer.echo(f'   stderr:\n{stderrf}')
    return {'exit': exitcode,
            'stdout': stdout.decode('ascii'),
            'stderr': stderr.decode('ascii')}


def straceApp(tag):
    ret = {}
    (exitcode, stdout, stderr) = execute(
        ['docker', 'exec', tag,
         'strace', '-f', '-e', 'trace=file,process,network,ipc', './app'])
    ret['critical'] = stderr.decode('ascii')
    print(stderr)
    (exitcode, stdout, stderr) = execute(
        ['docker', 'exec', tag, 'strace', '-f', '-c', './app'])
    ret['summary'] = stderr.decode('ascii')
    return ret


def getDiff(tag):
    (exitcode, stdout, stderr) = execute(['docker', 'diff', tag])
    if stderr:
        stderr = typer.style(stderr.decode('ascii'), fg=typer.colors.RED)
        typer.echo('Failed to diff container:')
        typer.echo(f'   tag:{tag}')
        typer.echo(f'   stderr:\n{stderr}')
        exit(1)
    else:
        diffs = str.strip(stdout.decode('ascii')).split('\n')
        diffs = [str.strip(line) for line in diffs]
        if len(diffs) == 2:
            diffs = []
        else:
            diffs.remove('A /root/app')
            rootChangeCount = reduce(
                lambda acc, s: 1 if ' /root/' in s else 0, diffs)
            if rootChangeCount < 1:
                diffs.remove('C /root')
        typer.echo('Filesystem changes:')
        typer.echo(f'   {diffs}')

    if not diffs:
        return
    typer.echo('Added file content:')
    files = {}
    for diff in diffs:
        if diff[0] == 'C':
            continue
        path = diff[2:]
        (exitcode, stdout, stderr) = execute(
            ['docker', 'exec', tag, 'cat', path])
        if stderr:
            stderr = stderr.decode('ascii')
            if 'Is a directory' in stderr:
                typer.echo(f'   {path}: dir')
                files[path] = 'dir'
            else:
                typer.echo(f'   error: {stderr}')
        else:
            typer.echo(f'   {path}: {stdout}')
            files[path] = stdout.decode('ascii')
    return {'docker-diff': diffs, 'diff-content': files}


def dumpResult(array):
    pass


def toMarkdown(object):
    pass


def dumpFiles(report, output_dir):
    for name, metrics in report.items():
        gAppDumpDir = join(output_dir, name)
        if exists(gAppDumpDir):
            shutil.rmtree(gAppDumpDir)
        mkdir(gAppDumpDir)
        if metrics['filesystem']:
            gFsDir = join(gAppDumpDir, 'filesystem')
            mkdir(gFsDir)
            for path, content in metrics['filesystem']['diff-content'].items():
                gPath = gFsDir + path
                if content == 'dir':
                    makedirs(gPath, exist_ok=True)
                else:
                    makedirs(dirname(gPath), exist_ok=True)
                    with open(gPath, 'w') as f:
                        f.write(content)
        gStraceDir = join(gAppDumpDir, 'strace')
        mkdir(gStraceDir)
        with open(join(gStraceDir, 'raw.txt'), 'w') as f:
            f.write(metrics['strace']['raw'])
        with open(join(gStraceDir, 'summary.txt'), 'w') as f:
            f.write(metrics['strace']['summary'])


def dumpMarkdown(report, output_dir):
    def trim(s, n):
        if not s:
            return s
        ret = s
        if len(ret) > n:
            ret = ret[0:800] + '\n...'
        return ret

    if exists(output_dir):
        remove(output_dir)
    mdFile = MdUtils(file_name=output_dir)
    mdFile.new_header(1, 'CS577 Report for Type II Binaries')
    mdFile.new_paragraph(
        "This is a sanbox analysis report auto generated by Layrex")

    mdFile.new_header(2, 'Overview')
    overviewTable = [
        'binary',
        'cracked',
        'filesystem activity',
        'network activity',
        'process forks']
    rowCounter = 1
    for name, metrics in report.items():
        cracked = ''
        fsActivity = 'Yes' if metrics['filesystem'] else 'No'
        netActivity = 'Yes' if 'sock' in metrics['strace']['summary'] else 'No'
        procForks = ''
        overviewTable.extend(
            [name, cracked, fsActivity, netActivity, procForks])
        rowCounter = rowCounter + 1
    mdFile.new_table(5, rowCounter, text=overviewTable)

    for name, metrics in report.items():
        mdFile.new_header(2, f'Analysis of {name}')

        mdFile.new_header(3, 'Process:')
        processInfo = metrics['process']

        normal = True
        if processInfo['exit'] != 0:
            mdFile.new_header(4, 'exit code: ' + str(processInfo['exit']))
            normal = False
        if processInfo['stdout']:
            mdFile.new_header(4, 'stdout:')
            mdFile.insert_code(trim(processInfo['stdout'], 300))
            normal = False
        if processInfo['stderr']:
            mdFile.new_header(4, 'stderr:')
            mdFile.insert_code(trim(processInfo['stderr'], 300))
            normal = False
        if normal:
            mdFile.new_paragraph(
                'The process exited with code 0, '
                'and no `stdout` or `stderr` was produced')

        mdFile.new_header(3, 'Filesystem:')
        if metrics['filesystem']:
            mdFile.new_header(4, 'Changes Observed:')

            # for entry in metrics['filesystem']['docker-diff']:
            mdFile.new_list(metrics['filesystem']['docker-diff'])
            mdFile.new_header(4, 'Changes Detail:')

            for name, content in metrics['filesystem']['diff-content'].items():
                text = [f'Added file `{name}` with the following content:']
                body = content
                if len(body) > 800:
                    body = body[0:800] + '\n...'

                mdFile.new_list(text)
                mdFile.insert_code(body, language='diff')
        else:
            mdFile.new_paragraph('No filesystem changes observed.')
        mdFile.new_header(3, 'Syscalls:')
        straceInfo = metrics['strace']
        mdFile.new_header(4, 'Summary:')
        mdFile.insert_code(straceInfo['summary'])
        mdFile.new_header(4, 'Critical Calls:')
        mdFile.insert_code(straceInfo['critical'])

        mdFile.new_header(3, 'Network:')
        networkInfo = metrics['tcpdump']
        if 'sock' in straceInfo['summary']:
            mdFile.insert_code(networkInfo['stdout'])
        else:
            mdFile.new_paragraph('No network traffic produced by the process.')
        # mdFile.insert_code(json.dumps(metrics))

    mdFile.create_md_file()


@app.command()
def dump(report_file: str,
         output_dir: str = typer.Option(..., '-o', help='Output directory'),
         format: str = typer.Option(
             ..., '-f', help='Dump file format [files | markdown]')):
    """
    Dumps json report to files or markdown
    """
    with open(report_file, 'r') as f:
        report = json.load(f)
    if format == 'files':
        dumpFiles(report, output_dir)
    elif format == 'markdown':
        dumpMarkdown(report, output_dir)
    else:
        exit(1)


@app.command()
def run(input_dir: str,
        output_dir: str):
    """
    Run through the binary in sandbox and generate a report in json
    """

    cleanUp()

    appLst = collectApps(input_dir)

    reportData = {}
    for name in appLst:
        appMetrics = {}
        title = typer.style(
            f'\n\nStart Analyzing: {name}',
            fg=typer.colors.GREEN,
            bold=True)
        typer.echo(title)
        binPath = abspath(join(input_dir, name))
        containerTag = SANDBOX_CONTAINER_PREFIX + name
        networkTag = SANDBOX_CONTAINER_PREFIX + name

        nicId = createNetwork(networkTag)
        sandbox = startSandbox(containerTag, networkTag)
        copyApp(containerTag, binPath)
        # appMetrics['process'] = execApp(sandbox, 'hzheng12')
        appMetrics['process'] = execApp(containerTag)
        appMetrics['filesystem'] = getDiff(containerTag)
        tcpdumpProc = startTcpdump(nicId, '')
        appMetrics['strace'] = straceApp(containerTag)
        killSandbox(sandbox)
        removeNetwork(networkTag)
        appMetrics['tcpdump'] = getRawTcpdump(tcpdumpProc)
        reportData[name] = appMetrics

    reportJson = json.dumps(reportData, sort_keys=True, indent=4)
    with open(join(output_dir, 'report.json'), 'w') as f:
        f.write(reportJson)


def main():
    app()
