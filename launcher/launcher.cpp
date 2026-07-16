#define _WIN32_WINNT 0x0A00
#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#define _CRT_SECURE_NO_WARNINGS

#include <windows.h>
#include <winhttp.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <shellapi.h>
#include <objbase.h>
#include <shobjidl.h>

#include <cstdio>
#include <cstdlib>
#include <cwchar>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <filesystem>
#include <conio.h>

namespace fs = std::filesystem;
#define VERSION "v0.3.1"
// 前向声明
int InstallFlow(std::wstring projDir);
int LaunchFlow(const std::wstring &projDir);

// ─── 控制台输出 ─────────────────────────────────────

static HANDLE g_hCon = GetStdHandle(STD_OUTPUT_HANDLE);

enum
{
    C_GREEN = 0x0A,
    C_RED = 0x0C,
    C_YELLOW = 0x0E,
    C_CYAN = 0x0B,
    C_WHITE = 0x07,
    C_BRIGHT = 0x0F
};

void SetColor(int c) { SetConsoleTextAttribute(g_hCon, c); }
void Print(const char *s)
{
    DWORD n;
    WriteConsoleA(g_hCon, s, (DWORD)strlen(s), &n, nullptr);
}

void PrintColor(int c, const char *s)
{
    SetColor(c);
    Print(s);
    SetColor(C_WHITE);
}

void Printf(const char *fmt, ...)
{
    char buf[4096];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    Print(buf);
}

void PrintfColor(int c, const char *fmt, ...)
{
    char buf[4096];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    SetColor(c);
    Print(buf);
    SetColor(C_WHITE);
}

void PrintHeader(const char *title)
{
    Print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    Print("  ");
    PrintColor(C_BRIGHT, title);
    Print("\n");
    Print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}

void PrintBanner()
{
    PrintColor(C_CYAN, "╔══════════════════════════════════════════╗\n");
    PrintColor(C_CYAN, "║  ");
    PrintColor(C_BRIGHT, "PaceTrace 行迹  启动器  " VERSION);
    PrintColor(C_CYAN, "          ║\n");
    PrintColor(C_CYAN, "╚══════════════════════════════════════════╝\n");
}

void PauseGet()
{
    Print("\n  请按 Enter 继续...");
    while (_getch() != '\r');
}

void PauseExit(int code)
{
    Print("\n  请按 Enter 退出...");
    char buf[64];
    fgets(buf, sizeof(buf), stdin);
    exit(code);
}

bool YesNo(const char *prompt)
{
    Printf("  %s (Y/n): ", prompt);
    char buf[16];
    fgets(buf, sizeof(buf), stdin);
    for (char *p = buf; *p; p++)
    {
        if (*p == '\n' || *p == '\r')
        {
            *p = 0;
            break;
        }
    }
    return buf[0] == 0 || buf[0] == 'y' || buf[0] == 'Y';
}

std::string ReadLine()
{
    char buf[1024];
    if (!fgets(buf, sizeof(buf), stdin))
        return "";
    for (char *p = buf; *p; p++)
    {
        if (*p == '\n' || *p == '\r')
        {
            *p = 0;
            break;
        }
    }
    return std::string(buf);
}

// ─── 路径工具 ─────────────────────────────────────────

std::wstring GetExeDir()
{
    wchar_t path[2048];
    GetModuleFileNameW(nullptr, path, 2048);
    PathRemoveFileSpecW(path);
    return path;
}

std::wstring GetProjectRoot()
{
    // 项目根目录就是 exe 所在目录，不爬父目录
    return GetExeDir();
}

bool FileExists(const std::wstring &path)
{
    return GetFileAttributesW(path.c_str()) != INVALID_FILE_ATTRIBUTES;
}

bool DirExists(const std::wstring &path)
{
    DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY);
}

// ─── 进程工具 ──────────────────────────────────────────

struct CmdResult
{
    int exitCode;
    std::string output;
};

CmdResult RunCapture(const std::wstring &cmd)
{
    CmdResult r = {-1, ""};
    SECURITY_ATTRIBUTES sa = {sizeof(sa), nullptr, TRUE};
    HANDLE hRead, hWrite;
    if (!CreatePipe(&hRead, &hWrite, &sa, 0))
        return r;

    STARTUPINFOW si = {sizeof(si)};
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdOutput = hWrite;
    si.hStdError = hWrite;

    PROCESS_INFORMATION pi = {0};
    std::wstring mutableCmd = cmd;
    BOOL ok = CreateProcessW(nullptr, &mutableCmd[0], nullptr, nullptr, TRUE,
                             CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi);
    CloseHandle(hWrite);

    if (!ok)
    {
        CloseHandle(hRead);
        return r;
    }

    CloseHandle(pi.hThread);

    char buf[4096];
    DWORD read;
    while (ReadFile(hRead, buf, sizeof(buf) - 1, &read, nullptr) && read > 0)
    {
        buf[read] = 0;
        r.output += buf;
    }
    CloseHandle(hRead);

    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD ec = 0;
    GetExitCodeProcess(pi.hProcess, &ec);
    r.exitCode = (int)ec;
    CloseHandle(pi.hProcess);
    return r;
}

int RunPassthrough(const std::wstring &cmd)
{
    STARTUPINFOW si = {sizeof(si)};
    PROCESS_INFORMATION pi = {0};
    std::wstring mutableCmd = cmd;
    if (!CreateProcessW(nullptr, &mutableCmd[0], nullptr, nullptr, TRUE,
                        0, nullptr, nullptr, &si, &pi))
    {
        PrintfColor(C_RED, "  命令失败: %ls\n", cmd.c_str());
        return -1;
    }
    CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD ec = 0;
    GetExitCodeProcess(pi.hProcess, &ec);
    CloseHandle(pi.hProcess);
    return (int)ec;
}

bool FindExe(const std::wstring &name)
{
    std::wstring cmd = L"where " + name + L" >nul 2>nul";
    return RunCapture(cmd).exitCode == 0;
}

// ─── HTTP 下载（WinHTTP）─────────────────────────────

bool HttpDownload(const std::wstring &url, const std::wstring &dest)
{
    URL_COMPONENTSW uc = {0};
    uc.dwStructSize = sizeof(uc);
    uc.dwSchemeLength = (DWORD)-1;
    uc.dwHostNameLength = (DWORD)-1;
    uc.dwUrlPathLength = (DWORD)-1;
    uc.dwExtraInfoLength = (DWORD)-1;

    if (!WinHttpCrackUrl(url.c_str(), (DWORD)url.size(), 0, &uc))
        return false;

    std::wstring scheme(uc.lpszScheme, uc.dwSchemeLength);
    std::wstring host(uc.lpszHostName, uc.dwHostNameLength);
    std::wstring path(uc.lpszUrlPath, uc.dwUrlPathLength);
    if (uc.lpszExtraInfo && uc.dwExtraInfoLength > 0)
        path += std::wstring(uc.lpszExtraInfo, uc.dwExtraInfoLength);

    HINTERNET hSession = WinHttpOpen(L"PaceTrace-Setup/1.0",
                                     WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, nullptr, nullptr, 0);
    if (!hSession)
        return false;

    HINTERNET hConnect = WinHttpConnect(hSession, host.c_str(), uc.nPort, 0);
    if (!hConnect)
    {
        WinHttpCloseHandle(hSession);
        return false;
    }

    DWORD flags = (scheme == L"https") ? WINHTTP_FLAG_SECURE : 0;
    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"GET", path.c_str(),
                                            nullptr, nullptr, nullptr, flags);
    if (!hRequest)
    {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return false;
    }

    BOOL sent = WinHttpSendRequest(hRequest,
                                   WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                                   WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
    if (!sent)
    {
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return false;
    }
    WinHttpReceiveResponse(hRequest, nullptr);

    HANDLE hFile = CreateFileW(dest.c_str(), GENERIC_WRITE, 0, nullptr,
                               CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hFile == INVALID_HANDLE_VALUE)
    {
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return false;
    }

    DWORD dwSize = 0;
    BYTE buffer[8192];
    while (WinHttpReadData(hRequest, buffer, sizeof(buffer), &dwSize) && dwSize > 0)
    {
        DWORD written;
        WriteFile(hFile, buffer, dwSize, &written, nullptr);
    }

    CloseHandle(hFile);
    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
    return true;
}

// ─── UV 管理 ───────────────────────────────────────────

bool IsUvInstalled()
{
    return FindExe(L"uv");
}

bool InstallUv()
{
    Print("  下载 uv 安装脚本...\n");

    wchar_t tmpDir[2048];
    GetTempPathW(2048, tmpDir);
    std::wstring scriptPath = std::wstring(tmpDir) + L"install-uv.ps1";

    bool ok = HttpDownload(L"https://astral.sh/uv/install.ps1", scriptPath);
    if (!ok)
    {
        PrintfColor(C_RED, "  下载失败，请检查网络\n");
        return false;
    }

    Print("  执行 uv 安装脚本...\n");
    std::wstring psCmd = L"powershell -ExecutionPolicy ByPass -File \"" + scriptPath + L"\"";
    int ec = RunPassthrough(psCmd);

    if (ec != 0)
    {
        PrintfColor(C_RED, "  uv 安装失败\n");
        return false;
    }

    // uv 安装到 %USERPROFILE%\.local\bin\uv.exe
    wchar_t profile[2048];
    GetEnvironmentVariableW(L"USERPROFILE", profile, 2048);
    std::wstring uvPath = std::wstring(profile) + L"\\.local\\bin\\uv.exe";
    if (!FileExists(uvPath))
    {
        PrintfColor(C_RED, "  uv 安装后未找到可执行文件\n");
        return false;
    }

    // 加入当前会话 PATH
    std::wstring binDir = uvPath.substr(0, uvPath.find_last_of(L"\\/"));
    std::wstring curPath;
    wchar_t pathBuf[32768];
    if (GetEnvironmentVariableW(L"PATH", pathBuf, 32768))
    {
        curPath = pathBuf;
    }
    std::wstring newPath = binDir + L";" + curPath;
    SetEnvironmentVariableW(L"PATH", newPath.c_str());

    PrintfColor(C_GREEN, "  uv 安装完成\n");
    return true;
}

// ─── Git 操作 ──────────────────────────────────────

int GitClone(const std::wstring &url, const std::wstring &branch, const std::wstring &dest)
{
    Print("  克隆仓库...\n");
    std::wstring cmd = L"git clone --branch " + branch + L" --depth 1 \"" + url + L"\" \"" + dest + L"\"";
    return RunPassthrough(cmd);
}

int GitPull(const std::wstring &repoDir, const std::wstring &branch)
{
    Print("  强制更新代码（将覆盖本地修改）...\n");
    std::wstring cmd = L"git -C \"" + repoDir + L"\" fetch --all"
        + L" && git -C \"" + repoDir + L"\" reset --hard origin/" + branch;
    return RunPassthrough(cmd);
}

// ─── 文件操作 ─────────────────────────────────────────

void CopyEnvExample(const std::wstring &projDir)
{
    auto example = projDir + L"\\.env.example";
    auto env = projDir + L"\\.env";

    if (!FileExists(example))
    {
        PrintfColor(C_YELLOW, "  .env.example 不存在，跳过\n");
        return;
    }
    if (FileExists(env))
    {
        Print("  .env 已存在，跳过\n");
        return;
    }

    if (CopyFileW(example.c_str(), env.c_str(), TRUE))
    {
        PrintfColor(C_GREEN, "  .env.example → .env  创建完成\n");
        PrintColor(C_YELLOW, "  请编辑 .env 填入 API 密钥\n");
    }
    else
    {
        PrintfColor(C_RED, "  复制 .env 失败\n");
    }
}

bool DeleteDirectory(const std::wstring &path)
{
    // 先切到 temp 目录，释放对项目目录的 cwd 锁
    wchar_t tmp[MAX_PATH];
    GetTempPathW(MAX_PATH, tmp);
    SetCurrentDirectoryW(tmp);

    for (int i = 0; i < 3; i++)
    {
        std::wstring cmd = L"cmd.exe /c rmdir /s /q \"" + path + L"\"";
        int ec = RunPassthrough(cmd);
        if (ec == 0 && !DirExists(path))
            return true;
        if (i < 2)
            Sleep(1000);
    }
    return false;
}

// ─── 创建快捷方式（开机启动）──────────────────────

bool CreateStartupShortcut(const std::wstring &targetExe, const std::wstring &args,
                           const std::wstring &workingDir, const std::wstring &desc)
{
    HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    if (FAILED(hr))
        return false;

    IShellLinkW *psl = nullptr;
    hr = CoCreateInstance(CLSID_ShellLink, nullptr, CLSCTX_INPROC_SERVER,
                          IID_IShellLinkW, (void **)&psl);
    if (FAILED(hr))
    {
        CoUninitialize();
        return false;
    }

    psl->SetPath(targetExe.c_str());
    psl->SetArguments(args.c_str());
    psl->SetWorkingDirectory(workingDir.c_str());
    psl->SetDescription(desc.c_str());

    IPersistFile *ppf = nullptr;
    hr = psl->QueryInterface(IID_IPersistFile, (void **)&ppf);
    if (FAILED(hr))
    {
        psl->Release();
        CoUninitialize();
        return false;
    }

    wchar_t startupPath[2048];
    SHGetSpecialFolderPathW(nullptr, startupPath, CSIDL_STARTUP, FALSE);
    std::wstring linkPath = std::wstring(startupPath) + L"\\PaceTrace.lnk";

    hr = ppf->Save(linkPath.c_str(), TRUE);
    ppf->Release();
    psl->Release();
    CoUninitialize();

    return SUCCEEDED(hr);
}

// ─── 安装流程 ────────────────────────────────────

struct InstallConfig
{
    std::wstring repoUrl = L"https://gitee.com/pfolg/pacetrace.git";
    std::wstring branch = L"main";
    std::wstring mirror = L"https://pypi.tuna.tsinghua.edu.cn/simple";
    std::wstring projDir;
};

bool IsInsideRepo(const std::wstring &dir)
{
    auto gitDir = dir + L"\\.git";
    return FileExists(gitDir) || DirExists(gitDir);
}

int InstallFlow(std::wstring projDir)
{
    InstallConfig cfg;
    cfg.projDir = projDir;

    // ── [1/4] 检查 uv + Git ──
    PrintHeader("1/4 检查环境");

    if (!IsUvInstalled())
    {
        PrintfColor(C_YELLOW, "  uv 未安装\n");
        if (!YesNo("是否自动安装 uv？"))
        {
            PrintfColor(C_RED, "  取消安装\n");
            return 1;
        }
        if (!InstallUv())
        {
            PauseExit(1);
        }
    }
    else
    {
        PrintfColor(C_GREEN, "  uv 已安装\n");
    }

    Print("  检查 Git...\n");
    if (!FindExe(L"git"))
    {
        PrintfColor(C_RED, "  未找到 Git，请先安装: https://git-scm.com/downloads\n");
        PauseExit(1);
    }
    PrintfColor(C_GREEN, "  Git 已安装\n");

    // ── [2/4] 仓库源 + 分支 ──
    PrintHeader("2/4 仓库源 + 分支");

    Print("  请选择仓库源:\n");
    Print("    1. GitHub  (github.com/igugyj/pacetrace)\n");
    Print("    2. Gitee   (gitee.com/pfolg/pacetrace) [默认]\n");
    Print("    3. 自定义\n");
    Print("  请输入 (1/2/3，默认 2): ");
    std::string repoOpt = ReadLine();
    if (repoOpt == "1")
        cfg.repoUrl = L"https://github.com/igugyj/pacetrace.git";
    else if (repoOpt == "3")
    {
        Print("  请输入仓库 URL: ");
        auto customUrl = ReadLine();
        if (!customUrl.empty())
        {
            int len = MultiByteToWideChar(CP_UTF8, 0, customUrl.c_str(), -1, nullptr, 0);
            cfg.repoUrl.resize(len);
            MultiByteToWideChar(CP_UTF8, 0, customUrl.c_str(), -1, &cfg.repoUrl[0], len);
            cfg.repoUrl.resize(len - 1);
        }
    }

    Print("  请输入分支名（默认 main）: ");
    std::string branchStr = ReadLine();
    if (!branchStr.empty())
    {
        int len = MultiByteToWideChar(CP_UTF8, 0, branchStr.c_str(), -1, nullptr, 0);
        cfg.branch.resize(len);
        MultiByteToWideChar(CP_UTF8, 0, branchStr.c_str(), -1, &cfg.branch[0], len);
        cfg.branch.resize(len - 1);
    }

    // ── [3/4] Git 同步 + .env ──
    PrintHeader("3/4 克隆 / 更新代码");

    if (!YesNo("同步代码？"))
    {
        Print("  跳过\n");
    }
    else
    {
        if (IsInsideRepo(cfg.projDir))
        {
            GitPull(cfg.projDir, cfg.branch);
        }
        else
        {
            int ec = GitClone(cfg.repoUrl, cfg.branch, cfg.projDir);
            if (ec != 0)
            {
                PrintfColor(C_RED, "  克隆失败\n");
                PauseExit(1);
            }
        }

        if (!FileExists(cfg.projDir + L"\\run.py"))
        {
            PrintfColor(C_RED, "  run.py 未找到，代码获取失败\n");
            PauseExit(1);
        }
        PrintfColor(C_GREEN, "  代码同步完成\n");
    }

    CopyEnvExample(cfg.projDir);

    // ── [4/4] uv sync ──
    PrintHeader("4/4 安装依赖");

    Printf("  uv sync --index-url %ls\n", cfg.mirror.c_str());
    std::wstring cmd = L"uv sync --directory \"" + cfg.projDir + L"\" --index-url " + cfg.mirror;
    int ec = RunPassthrough(cmd);
    if (ec != 0)
    {
        PrintfColor(C_RED, "  uv sync 失败\n");
        PauseExit(1);
    }
    PrintfColor(C_GREEN, "  依赖安装完成\n");

    PrintfColor(C_GREEN, "\n  ✓ 安装完成\n");

    if (YesNo("现在启动 PaceTrace？"))
    {
        LaunchFlow(cfg.projDir);
    }

    return 0;
}

// ─── 启动流程 ──────────────────────────────────────────

int LaunchFlow(const std::wstring &projDir)
{
    auto runPy = projDir + L"\\run.py";
    if (!FileExists(runPy))
    {
        PrintfColor(C_RED, "  run.py 未找到: %ls\n", runPy.c_str());
        PauseExit(1);
    }

    CopyEnvExample(projDir);

    PrintfColor(C_GREEN, "\n  PaceTrace 启动中...\n");
    Print("  主界面:   http://localhost:8501\n");
    Print("  轨迹画板: http://localhost:8852/drawer.html\n");
    Print("  Ctrl+C 停止\n\n");

    std::wstring cmd = L"uv run --directory \"" + projDir + L"\" python run.py";
    int ec = RunPassthrough(cmd);

    Printf("\n  程序已退出（返回码 %d）\n", ec);
    PauseGet();
    return ec;
}

// ─── 菜单 ────────────────────────────────────────────────

void ShowMenu()
{
    PrintBanner();
    Print("  1  完整安装 / 更新\n");
    Print("  2  直接启动\n");
    Print("  3  添加到开机启动\n");
    Print("  4  卸载\n");
    Print("  5  退出\n");
    Print("\n  请选择 (1/2/3/4/5): ");
}

// ─── 入口 ────────────────────────────────────────────────

int main()
{
    // UTF-8 代码页
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);

    auto projRoot = GetProjectRoot();
    auto projDir = projRoot + L"\\PaceTrace";

    while (true)
    {
        system("cls");
        ShowMenu();
        std::string opt = ReadLine();
        int choice = opt.empty() ? 0 : opt[0] - '0';

        switch (choice)
        {
        case 1:
            InstallFlow(projDir);
            break;
        case 2:
            LaunchFlow(projDir);
            break;
        case 3:
        {
            wchar_t exePath[2048];
            GetModuleFileNameW(nullptr, exePath, 2048);
            bool ok = CreateStartupShortcut(exePath, L"--launch", projDir,
                                            L"PaceTrace - 自动启动");
            if (ok)
                PrintfColor(C_GREEN, "  开机启动添加成功\n");
            else
                PrintfColor(C_RED, "  添加失败\n");
            PauseGet();
            break;
        }
        case 4:
        {
            auto targetDir = projDir;
            Printf("  即将删除: %ls\n", targetDir.c_str());
            if (YesNo("确认删除？"))
            {
                if (DeleteDirectory(targetDir))
                    PrintfColor(C_GREEN, "  删除成功\n");
                else
                    PrintfColor(C_RED, "  删除失败\n");
            }
            PauseGet();
            break;
        }
        case 5:
            return 0;
        default:
            break;
        }
    }

    return 0;
}
