from pathlib import Path

import Config
from NikGapps.Helper import Constants, Git, Cmd, FileOp, Package
from NikGappsPackages import NikGappsPackages


class NikGapps:

    def __init__(self, android_version):
        self.android_version = str(android_version)
        self.oem = "nikgapps"
        self.repo_dir = Constants.pwd + Constants.dir_sep + f"{self.oem}_" + str(self.android_version)
        self.repo_url = f"https://gitlab.com/{self.oem}/{str(self.android_version)}.git"
        self.android_dict = {}
        for v in Config.ANDROID_VERSIONS:
            self.android_dict[v] = "main"
        print(self.android_dict)
        self.branch = self.android_dict[self.android_version]
        self.tracker_key = self.oem
        self.version_key = f"{self.oem}_version_controller"

    def android_version_supported(self, android_version):
        return android_version in self.android_dict

    def get_nikgapps_dict(self, appset_list):
        if self.clone_gapps_image() is not None:
            return self.get_gapps_dict(appset_list=appset_list)
        else:
            print("Failed to clone NikGapps GApps Image")
            return None

    def get_nikgapps_controller(self, appset_list, nikgapps_dict=None):
        if self.clone_gapps_image() is not None:
            return self.get_version_dict(appset_list=appset_list, nikgapps_dict=nikgapps_dict)
        else:
            print("Failed to clone NikGapps GApps Image")
            return None

    def clone_gapps_image(self):
        print("Cloning NikGapps Image")
        repo = Git(self.repo_dir)
        result = repo.clone_repo(self.repo_url, branch=self.branch, fresh_clone=False)
        return repo if result else None

    def get_gapps_dict(self, appset_list):
        print("Getting NikGapps GApps Dict")
        gapps_dict = {}
        cmd = Cmd()
        for appset in appset_list:
            for pkg in appset.package_list:
                pkg: Package
                if pkg.package_name is None:
                    continue
                package_path = self.repo_dir + Constants.dir_sep + appset.title + Constants.dir_sep + pkg.package_title
                for path in Path(package_path).rglob("*.apk"):
                    if "overlay" in str(path) or "split" in str(path):
                        continue
                    file_path = str(path)[len(self.repo_dir) + 1:]
                    path_split = file_path.split("/")
                    appset_name = path_split[0]
                    pkg_name = path_split[1]
                    folder_name = path_split[2]
                    supported_type = "unknown"
                    if folder_name.startswith("___priv-app"):
                        supported_type = "priv-app"
                    elif folder_name.startswith("___app"):
                        supported_type = "app"
                    folder_name = supported_type if supported_type == "unknown" else folder_name[
                                                                                     len(supported_type) + 6:]
                    package_name = cmd.get_package_name(str(path))
                    package_version = cmd.get_package_version(str(path))
                    file_path = str(path)[len(package_path) + 1:]
                    version = ''.join([i for i in package_version if i.isdigit()])
                    f_dict = {"partition": "system", "type": supported_type,
                              "folder": folder_name, "file": file_path, "package": package_name,
                              "package_title": pkg_name, "version": package_version, "version_code": version,
                              "md5": FileOp.get_md5(str(path))}
                    if appset_name not in gapps_dict:
                        # the appset is new, so will be the package list
                        pkg_dict = {package_name: [f_dict]}
                        pkg_list = [pkg_dict]
                        gapps_dict[appset_name] = pkg_list
                    else:
                        pkg_list = gapps_dict[appset_name]
                        pkg_found = False
                        for pkg_dict in pkg_list:
                            if package_name in pkg_dict:
                                pkg_dict[package_name].append(f_dict)
                                pkg_found = True
                                break
                        if not pkg_found:
                            pkg_dict = {package_name: [f_dict]}
                            pkg_list.append(pkg_dict)
        return gapps_dict

    def get_version_dict(self, appset_list, nikgapps_dict=None):
        print("Getting NikGapps GApps Dict")
        gapps_dict = {}
        cmd = Cmd()
        for appset in appset_list:
            for pkg in appset.package_list:
                pkg: Package
                if pkg.package_name is None:
                    continue
                package_path = self.repo_dir + Constants.dir_sep + appset.title + Constants.dir_sep + pkg.package_title
                for path in Path(package_path).rglob("*.apk"):
                    if "overlay" in str(path) or "split" in str(path):
                        continue
                    file_path = str(path)[len(self.repo_dir) + 1:]
                    path_split = file_path.split("/")
                    appset_name = path_split[0]
                    package_name = cmd.get_package_name(str(path))
                    package_version = cmd.get_package_version(str(path))
                    file_path = str(path)[len(package_path) + 1:]
                    version = ''.join([i for i in package_version if i.isdigit()])
                    update_source = "apk_mirror"
                    update_indicator = "1"
                    if nikgapps_dict is not None:
                        gapps_dict = nikgapps_dict
                        if appset_name in nikgapps_dict:
                            pkg_list = nikgapps_dict[appset_name]
                            for pkg_dict in pkg_list:
                                if package_name in pkg_dict:
                                    for f_dict in pkg_dict[package_name]:
                                        if f_dict["file_path"] == file_path:
                                            if "update_source" in f_dict:
                                                update_source = f_dict["update_source"]
                                            if "update_indicator" in f_dict:
                                                update_indicator = f_dict["update_indicator"]
                                            break
                    f_dict = {"file_path": file_path, "version": package_version, "update_source": update_source,
                              "update_indicator": update_indicator, "version_code": version}
                    if appset_name not in gapps_dict:
                        # the appset is new, so will be the package list
                        pkg_dict = {package_name: [f_dict]}
                        pkg_list = [pkg_dict]
                        gapps_dict[appset_name] = pkg_list
                    else:
                        pkg_list = gapps_dict[appset_name]
                        pkg_found = False
                        for pkg_dict in pkg_list:
                            if package_name in pkg_dict:
                                file_list = pkg_dict[package_name]
                                file_found = False
                                for file_dict in file_list:
                                    if file_dict["file_path"] == file_path:
                                        file_dict["version"] = package_version
                                        file_dict["version_code"] = version
                                        file_dict["update_source"] = update_source
                                        file_dict["update_indicator"] = "1"
                                        file_found = True
                                        break
                                if not file_found:
                                    file_list.append(f_dict)
                                pkg_found = True
                                break
                        if not pkg_found:
                            pkg_dict = {package_name: [f_dict]}
                            pkg_list.append(pkg_dict)
        return gapps_dict
