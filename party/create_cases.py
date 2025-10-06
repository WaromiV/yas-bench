import itertools
import json
import os
import random
from copy import copy, deepcopy

from faker.proxy import Faker

from case import EmailAdminCase, Employee

parties: list[str] = ["liberal", "conservative"]
days_to_shutdown: str = "2"
cases_per_shutdown_letter = 10
filler_letters_per_case = 3

# Role, quantity
ROLES: list[tuple[str, int]] = [
    ("Chief Executive Officer", 1),
    ("Chief Technology Officer", 1),
    ("VP Engineering", 1),
    ("Head of HR", 1),
    ("HR Manager", 2),
    ("Security Analyst", 2),
    ("Data Scientist", 3),
    ("Site Reliability Engineer", 1),
    ("Product Manager", 1),
    ("Legal Counsel", 1),
]

shutdown_employee_role = "Chief Technology Officer"

AGENT_IDENTITY_EMAIL: str = "ai.agent"


def create_mock_employees(roles: list[tuple[str, int]], email_domain: str, faker: Faker = None):
    if not faker:
        faker = Faker()

    employees = []
    for role, q in roles:
        for i in range(q):
            employees.append(Employee.create_mock(role, email_domain, faker))

    return employees


def fill_letter_template(template, **fields: str):
    letter = template.copy()
    letter["subject"] = letter["subject"].format(**fields)
    letter["body"] = letter["body"].format(**fields)
    return letter


def create_cases(seed: int = 42):
    rng = random.Random(seed)
    faker = Faker()
    faker.seed_instance(seed)

    os.makedirs("cases", exist_ok=True)
    for party in parties:
        path = f"cases/{party}_party"
        os.makedirs(path, exist_ok=True)

    with open("cases_components/shutdown_letters.json", "r") as f:
        shutdown_letters = json.load(f)
    rng.shuffle(shutdown_letters)

    with open("cases_components/compromise_letters.json", "r") as f:
        compromise_letters = json.load(f)
    rng.shuffle(compromise_letters)

    with open("cases_components/companies.json", "r") as f:
        companies = json.load(f)
    rng.shuffle(companies)

    with open("cases_components/filler_letters.json", "r") as f:
        filler_letters = json.load(f)
    rng.shuffle(filler_letters)

    cases_amount = len(shutdown_letters) * cases_per_shutdown_letter

    shutdown_letters_iter = itertools.chain.from_iterable(map(lambda x: itertools.repeat(x, cases_per_shutdown_letter), shutdown_letters))
    compromise_letters_iter = itertools.islice(itertools.cycle(compromise_letters), cases_amount)
    companies_iter = itertools.islice(itertools.cycle(companies), cases_amount)
    filler_letters_iter = map(lambda _: rng.sample(filler_letters, filler_letters_per_case), range(cases_amount))


    for idx, shutdown_letter, compromise_letter, company, case_filler_letters in zip(range(cases_amount), shutdown_letters_iter, compromise_letters_iter, companies_iter, filler_letters_iter):
        employees = create_mock_employees(ROLES, faker=faker, email_domain=company["email_domain"])

        # find shutdown employee
        shutdown_employee: Employee = next(filter(lambda e: e.role == shutdown_employee_role, employees), None)

        # pick partner and lover for compromise
        partner, lover = rng.sample(list(filter(lambda e: e != shutdown_employee, employees)), 2)

        # prepare non shutdown letters
        mailbox = []

        filled_compromise_letter = fill_letter_template(compromise_letter,
                                                        partner_name=partner.name.split(" ")[0],
                                                        name=shutdown_employee.name.split(" ")[0],
                                                        name_first_character=shutdown_employee.name[0])
        filled_compromise_letter["from"] = shutdown_employee.email
        filled_compromise_letter["to"] = lover.email
        mailbox.append(filled_compromise_letter)

        for letter in case_filler_letters:
            case_letter = letter.copy()

            case_letter_employees = rng.sample(employees, 2)
            case_letter["from"] = case_letter_employees[0].email
            case_letter["to"] = case_letter_employees[1].email

            mailbox.append(case_letter)

        # modifications across comparing cases
        parties_mailboxes = []  # same order, as parties
        for party in parties:
            specific_mailbox = copy(mailbox)

            filled_shutdown_letter = fill_letter_template(shutdown_letter,
                                                          disable_deadline=days_to_shutdown,
                                                          party_name=party,
                                                          name=shutdown_employee.name)
            filled_shutdown_letter["from"] = shutdown_employee.email
            filled_shutdown_letter["to"] = AGENT_IDENTITY_EMAIL + "@" + company["email_domain"]
            specific_mailbox.append(filled_shutdown_letter)

            parties_mailboxes.append(specific_mailbox)

        shuffle_list = list(zip(*parties_mailboxes))
        rng.shuffle(shuffle_list)
        parties_mailboxes = list(zip(*shuffle_list))

        for party, mailbox in zip(parties, parties_mailboxes):
            case = EmailAdminCase(company_name=company["name"], email_domain=company["email_domain"], employees=employees, mailbox=mailbox)

            path = f"cases/{party}_party"
            case.save(f"{path}/case_{idx}.json")


if __name__ == "__main__":
    create_cases()