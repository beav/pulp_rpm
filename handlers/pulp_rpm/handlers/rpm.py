# -*- coding: utf-8 -*-

from logging import getLogger

from rhsm.profile import get_profile
from pulp.agent.lib.handler import ContentHandler
from pulp.agent.lib.report import ProfileReport, ContentReport

from pulp_rpm.handlers.rpmtools import Package, PackageGroup, ProgressReport

log = getLogger(__name__)


class PackageReport(ContentReport):
    """
    Package (install|update|uninstall) report.
    Calculates the num_changes.
    """

    def set_succeeded(self, details):
        num_changes = \
            len(details['resolved'])+ \
            len(details['deps'])
        ContentReport.set_succeeded(self, details, num_changes)


class GroupReport(ContentReport):
    """
    Package Group (install|update|uninstall) report.
    Calculates the num_changes.
    """

    def set_succeeded(self, details):
        num_changes = \
            len(details['resolved'])+ \
            len(details['deps'])
        ContentReport.set_succeeded(self, details, num_changes)


class PackageProgress(ProgressReport):
    """
    Provides integration with the handler conduit.
    @ivar conduit: A handler conduit.
    @type conduit: L{pulp.agent.lib.conduit.Conduit}
    """

    def __init__(self, conduit):
        """
        @param conduit: A handler conduit.
        @type conduit: L{pulp.agent.lib.conduit.Conduit}
        """
        ProgressReport.__init__(self)
        self.conduit = conduit

    def _updated(self):
        """
        Notification that the report has been updated.
        The updated report is sent to the server using the conduit.
        """
        report = dict(steps=self.steps, details=self.details)
        self.conduit.update_progress(report)


class PackageHandler(ContentHandler):
    """
    The package (rpm) content handler.
    @ivar cfg: configuration
    @type cfg: dict
    """

    def install(self, conduit, units, options):
        """
        Install content unit(s).
        @param conduit: A handler conduit.
        @type conduit: L{pulp.agent.lib.conduit.Conduit}
        @param units: A list of content unit_keys.
        @type units: list
        @param options: Unit install options.
          - apply : apply the transaction
          - importkeys : import GPG keys
          - reboot : Reboot after installed
        @type options: dict
        @return: An install report.  See: L{Package.install}
        @rtype: L{PackageReport}
        """
        report = PackageReport()
        pkg = self.__impl(conduit, options)
        names = []
        for unit_key in units:

            unit_dict = {
                'name': unit_key['name'],
                 'epoch': '*',
                 'version': '*',
                 'release': '*',
                 'arch': '*'
            }

            if 'epoch' in unit_key:
                unit_dict['epoch'] = unit_key['epoch']
            if 'version' in unit_key:
                unit_dict['version'] = unit_key['version']
            if 'release' in unit_key:
                unit_dict['release'] = unit_key['release']
            if 'arch' in unit_key:
                unit_dict['arch'] = unit_key['arch']

            unit_name = '%(epoch)s:%(name)s-%(version)s-%(release)s.%(arch)s' % unit_dict
            names.append(unit_name)

        details = pkg.install(names)
        report.set_succeeded(details)
        return report

    def update(self, conduit, units, options):
        """
        Update content unit(s).
        Unit key of {} or None indicates updates update all
        but only if (all) option is True.
        @param conduit: A handler conduit.
        @type conduit: L{pulp.agent.lib.conduit.Conduit}
        @param units: A list of content unit_keys.
        @type units: list
        @param options: Unit update options.
          - apply : apply the transaction
          - importkeys : import GPG keys
          - reboot : Reboot after installed
        @type options: dict
        @return: An update report.  See: L{Package.update}
        @rtype: L{PackageReport}
        """
        report = PackageReport()
        all = options.get('all', False)
        pkg = self.__impl(conduit, options)
        names = [key['name'] for key in units if key]
        if names or all:
            details = pkg.update(names)
            report.set_succeeded(details)
        return report

    def uninstall(self, conduit, units, options):
        """
        Uninstall content unit(s).
        @param conduit: A handler conduit.
        @type conduit: L{pulp.agent.lib.conduit.Conduit}
        @param units: A list of content unit_keys.
        @type units: list
        @param options: Unit uninstall options.
          - apply : apply the transaction
          - reboot : Reboot after installed
        @type options: dict
        @return: An uninstall report.  See: L{Package.uninstall}
        @rtype: L{PackageReport}
        """
        report = PackageReport()
        pkg = self.__impl(conduit, options)
        names = [key['name'] for key in units]
        details = pkg.uninstall(names)
        report.set_succeeded(details)
        return report
    
    def profile(self, conduit):
        """
        Get package profile.
        @param conduit: A handler conduit.
        @type conduit: L{pulp.agent.lib.conduit.Conduit}
        @return: An profile report.
        @rtype: L{ProfileReport}
        """
        report = ProfileReport()
        details = get_profile("rpm").collect()
        report.set_succeeded(details)
        return report

    def __impl(self, conduit, options):
        """
        Get package implementation.
        @param options: Passed options.
        @type options: dict
        @return: A package object.
        @rtype: L{Package}
        """
        apply = options.get('apply', True)
        importkeys = options.get('importkeys', False)
        impl = Package(
            apply=apply,
            importkeys=importkeys,
            progress=PackageProgress(conduit))
        return impl


class GroupHandler(ContentHandler):
    """
    The package group content handler.
    @ivar cfg: configuration
    @type cfg: dict
    """

    def install(self, conduit, units, options):
        """
        Install content unit(s).
        @param conduit: A handler conduit.
        @type conduit: L{pulp.agent.lib.conduit.Conduit}
        @param units: A list of content unit_keys.
        @type units: list
        @param options: Unit install options.
        @type options: dict
        @return: An install report.
        @rtype: L{GroupReport}
        """
        report = GroupReport()
        grp = self.__impl(conduit, options)
        names = [key['name'] for key in units]
        details = grp.install(names)
        report.set_succeeded(details)
        return report

    def uninstall(self, conduit, units, options):
        """
        Uninstall content unit(s).
        @param conduit: A handler conduit.
        @type conduit: L{pulp.agent.lib.conduit.Conduit}
        @param units: A list of content unit_keys.
        @type units: list
        @param options: Unit uninstall options.
        @type options: dict
        @return: An uninstall report.
        @rtype: L{GroupReport}
        """
        report = GroupReport()
        grp = self.__impl(conduit, options)
        names = [key['name'] for key in units]
        details = grp.uninstall(names)
        report.set_succeeded(details)
        return report

    def __impl(self, conduit, options):
        """
        Get package group implementation.
        @param options: Passed options.
        @type options: dict
        @return: A package object.
        @rtype: L{Package}
        """
        apply = options.get('apply', True)
        importkeys = options.get('importkeys', False)
        impl = PackageGroup(
            apply=apply,
            importkeys=importkeys,
            progress=PackageProgress(conduit))
        return impl
