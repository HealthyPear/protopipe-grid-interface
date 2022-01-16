"""
Select DIRAC jobs matching the given conditions and set them to failed if they are stuck.

This is a variation over the DIRAC script dirac-wms-select-jobs.
"""

import DIRAC
from DIRAC import gLogger
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Core.Utilities.DIRACScript import DIRACScript as Script
from DIRAC.WorkloadManagementSystem.Client.JobReport import JobReport


@Script()
def main():
    Script.registerSwitch("", "Status=", "Primary status")
    Script.registerSwitch("", "MinorStatus=", "Secondary status")
    Script.registerSwitch("", "ApplicationStatus=", "Application status")
    Script.registerSwitch("", "Site=", "Execution site")
    Script.registerSwitch("", "Owner=", "Owner (DIRAC nickname)")
    Script.registerSwitch("", "JobGroup=", "Select jobs for specified job group")
    Script.registerSwitch(
        "", "Date=", "Date in YYYY-MM-DD format, if not specified default is today"
    )
    switches, args = Script.parseCommandLine(ignoreErrors=True)

    # Default values
    status = None
    minor_status = None
    app_status = None
    site = None
    owner = None
    job_groups = []
    date = None

    if args:
        Script.showHelp()

    exit_code = 0

    for switch in switches:
        if switch[0].lower() == "status":
            status = switch[1]
        elif switch[0].lower() == "minorstatus":
            minor_status = switch[1]
        elif switch[0].lower() == "applicationstatus":
            app_status = switch[1]
        elif switch[0].lower() == "site":
            site = switch[1]
        elif switch[0].lower() == "owner":
            owner = switch[1]
        elif switch[0].lower() == "jobgroup":
            for jg in switch[1].split(","):
                if jg.isdigit():
                    job_groups.append(f"{int(jg)}")
                else:
                    job_groups.append(jg)
        elif switch[0].lower() == "date":
            date = switch[1]

    selected_date = date
    if not date:
        selected_date = "Today"
    conditions = {
        "Status": status,
        "MinorStatus": minor_status,
        "ApplicationStatus": app_status,
        "Owner": owner,
        "JobGroup": ",".join(str(jg) for jg in job_groups),
        "Date": selected_date,
    }

    dirac = Dirac()
    jobs = []

    if job_groups:
        for job_group in job_groups:
            res = dirac.selectJobs(
                status=status,
                minorStatus=minor_status,
                applicationStatus=app_status,
                site=site,
                owner=owner,
                jobGroup=job_group,
                date=date,
                printErrors=False,
            )
            if res["OK"]:
                jobs.extend(res["Value"])
            else:
                gLogger.error("Can't select jobs: ", res["Message"])
    else:
        res = dirac.selectJobs(
            status=status,
            minorStatus=minor_status,
            applicationStatus=app_status,
            site=site,
            owner=owner,
            date=date,
            printErrors=False,
        )
        if res["OK"]:
            jobs.extend(res["Value"])
        else:
            gLogger.error("Can't select jobs: ", res["Message"])

    conds = [f"{n} = {v}" for n, v in conditions.items() if v]
    constrained = " "

    if jobs:
        gLogger.notice(
            "==> Selected %s jobs%swith conditions: %s\n%s"
            % (len(jobs), constrained, ", ".join(conds), ",".join(jobs))
        )
    else:
        gLogger.notice("No jobs were selected with conditions:", ", ".join(conds))

    for job in jobs:
        job_report = JobReport(job)
        res = job_report.setJobStatus("Failed")
        if not res["OK"]:
            gLogger.error(res)

    DIRAC.exit(exit_code)


if __name__ == "__main__":
    main()
