import requests 
import urllib3
import re
from datetime import datetime
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # Configuration
HUB_TOKEN = os.getenv("HUB_TOKEN")
HUB_REPO = os.getenv("HUB_REPO")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
GITLAB_URL = os.getenv("GITLAB_URL")

github_headers = { 
    "Authorization": f"token {HUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
gitlab_headers = {
    "PRIVATE-TOKEN": GITLAB_TOKEN
}


def extract_external_id(comments, platform):
    """Extrait l'ID externe des commentaires."""
    comments_text = "\n".join(comment['body'] for comment in comments)  # Extraire le corps de chaque commentaire
    # Logique pour extraire l'ID basé sur la plateforme
    if platform == "GitHub":
        # Exemple d'extraction pour GitHub
        match = re.search(r"GitLab Issue ID: (\d+)", comments_text)
    elif platform == "GitLab":
        # Exemple d'extraction pour GitLab
        match = re.search(r"GitHub Issue ID: (\d+)", comments_text)
    
    return match.group(1) if match else None







def get_github_milestones():
    """Récupère les milestones depuis GitHub."""
    url = f"https://api.github.com/repos/{HUB_REPO}/milestones"
    response = requests.get(url, headers=github_headers)
    response.raise_for_status()
    return response.json()

def get_gitlab_milestones():
    """Récupère les milestones depuis GitLab."""
    url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/milestones"
    response = requests.get(url, headers=gitlab_headers, verify=False)
    response.raise_for_status()
    return response.json()

def sync_milestones():
    """Synchronise les milestones entre GitHub et GitLab."""
    github_milestones = get_github_milestones()
    gitlab_milestones = get_gitlab_milestones()

    trouve = 0

    # Cartographier les milestones par titre
    github_milestones_by_title = {m["title"]: m for m in github_milestones}
    gitlab_milestones_by_title = {m["title"]: m for m in gitlab_milestones}

    # Synchroniser GitHub → GitLab
    for milestone in github_milestones:
        if milestone["title"] not in gitlab_milestones_by_title:
            print(f"Création du milestone GitLab : {milestone['title']}")
            create_gitlab_milestone(milestone)
            trouve = 1

    # Synchroniser GitLab → GitHub
    for milestone in gitlab_milestones:
        if milestone["title"] not in github_milestones_by_title:
            print(f"Création du milestone GitHub : {milestone['title']}")
            create_github_milestone(milestone)

    if trouve == 1:
        print("Milestones synchronisés.")
    else:
        print("Milestones à jour.")

def create_github_milestone(milestone):
    """Crée un milestone sur GitHub."""
    url = f"https://api.github.com/repos/{HUB_REPO}/milestones"

    # Convertir le due_date de GitLab (YYYY-MM-DD) en due_on de GitHub (YYYY-MM-DDTHH:MM:SSZ)
    due_date = milestone.get("due_date")
    due_on = None
    if due_date:
        try:
            # Convertir la date GitLab en objet datetime
            due_datetime = datetime.strptime(due_date, "%Y-%m-%d")
            # Convertir en format GitHub (YYYY-MM-DDTHH:MM:SSZ)
            due_on = due_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
            print(f"Erreur lors de la conversion de la date : {e}")

    data = {
        "title": milestone["title"],
        "description": milestone.get("description", ""),
        "due_on": due_on  # Utiliser la date convertie
    }

    try:
        response = requests.post(url, headers=github_headers, json=data)
        response.raise_for_status()
        print(f"Milestone créé sur GitHub : {milestone['title']}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la création du milestone sur GitHub : {e}")
        print(f"Contenu de la réponse : {e.response.text}")  # Log de la réponse d'erreur

def create_gitlab_milestone(milestone):
    """Crée un milestone sur GitLab."""
    url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/milestones"
    data = {
        "title": milestone["title"],
        "description": milestone.get("description", ""),
        "due_date": milestone.get("due_on", None)  # Format : "YYYY-MM-DD"
    }
    
    try:
        response = requests.post(url, headers=gitlab_headers, json=data, verify=False)
        response.raise_for_status()
        print(f"Milestone créé sur GitLab : {milestone['title']}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la création du milestone sur GitLab : {e}")


def update_github_issue_with_milestone(issue, github_issue, milestone_title):
    """Met à jour une issue GitHub avec un milestone."""
    url = f"https://api.github.com/repos/{HUB_REPO}/issues/{github_issue['number']}"

    milestone_id = get_github_milestone_id_by_title(milestone_title)
    #if milestone_id != github_issue['milestone']['id']:
    if github_issue['milestone'] is not None and milestone_id != github_issue['milestone']['id']:
        data = {
            "milestone": milestone_id
        }
        print(f"Erreur lors de l'association du milestone sur GitLab : {e}")
        try:
            response = requests.patch(url, headers=github_headers, json=data)
            response.raise_for_status()
            print(f"Milestone associé à l'issue GitHub : {issue['title']}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'association du milestone sur GitHub : {e}")

    else:
        print(f"milestone déjà associé à l'issue : {issue['title']}")

def update_gitlab_issue_with_milestone(issue, gitlab_issue, milestone_title):

    """Met à jour une issue GitLab avec un milestone."""
    url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue['iid']}"
    milestone_id = get_gitlab_milestone_id_by_title(milestone_title)

    #if milestone_id != gitlab_issue['milestone']['id']:
    if gitlab_issue['milestone'] is not None and milestone_id != gitlab_issue['milestone']['id']:
    # Votre logique ici
        data = {
            "milestone_id": milestone_id
        }

        try:
            response = requests.put(url, headers=gitlab_headers, json=data, verify=False)
            response.raise_for_status()
            print(f"Milestone associé à l'issue GitLab : {issue['title']}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'association du milestone sur GitLab : {e}")

    else:
        print(f"milestone déjà associé à l'issue : {issue['title']}")

def get_github_milestone_id_by_title(title):
    """Récupère l'ID d'un milestone GitHub par son titre."""
    milestones = get_github_milestones()
    for milestone in milestones:
        if milestone["title"] == title:
            return milestone["number"]
    return None

def get_gitlab_milestone_id_by_title(title):
    """Récupère l'ID d'un milestone GitLab par son titre."""
    milestones = get_gitlab_milestones()
    for milestone in milestones:
        if milestone["title"] == title:
            return milestone["id"]
    return None

def find_issue_by_title(issues, title):
    """Recherche une issue par titre."""
    for issue in issues:
        if issue["title"] == title:
            return issue
    return None

def get_github_issues():
    """Récupère les issues depuis GitHub."""
    url = f"https://api.github.com/repos/{HUB_REPO}/issues?state=all"
    response = requests.get(url, headers=github_headers)
    response.raise_for_status()
    issues = response.json()
    
    # Ajouter les labels à chaque issue
    for issue in issues:
        issue["labels"] = [label["name"] for label in issue.get("labels", [])]
    
    return issues

def get_gitlab_issues():
    """Récupère les issues existantes depuis GitLab."""
    url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues?scope=all"
    response = requests.get(url, headers=gitlab_headers, verify=False)
    response.raise_for_status()
    issues = response.json()
    
    # Ajouter les labels à chaque issue
    for issue in issues:
        issue["labels"] = issue.get("labels", [])
    
    return issues

def convert_state_for_gitlab(state):
    """Convertit l'état de GitHub en état GitLab."""
    if state == "open":
        return "opened"
    elif state == "closed":
        return "closed"
    return state

def convert_state_for_github(state):
    """Convertit l'état de GitLab en état GitHub."""
    if state == "opened":
        return "open"
    elif state == "closed":
        return "closed"
    return state

def update_github_issue(issue, github_issue_number):
    """Met à jour une issue existante sur GitHub."""
    url = f"https://api.github.com/repos/{HUB_REPO}/issues/{github_issue_number}"
    data = {
        "title": issue["title"],
        "body": issue.get("description", "Pas de description"),  # Description sans l'ID
        "state": convert_state_for_github(issue["state"]),  # Convert state for GitHub
        "labels": issue.get("labels", [])  # Ajouter les labels
    }
    
    try:
        # Mise à jour de l'issue sur GitHub
        response = requests.patch(url, headers=github_headers, json=data)
        response.raise_for_status()
        github_issue = response.json()
        
        # Ajout d'un commentaire avec l'ID de l'issue GitLab
        comment_url = f"https://api.github.com/repos/{HUB_REPO}/issues/{github_issue_number}/comments"
        comment_data = {
            "body": f"GitLab Issue ID: {issue['iid']}"
        }
        comment_response = requests.post(comment_url, headers=github_headers, json=comment_data)
        comment_response.raise_for_status()
        
        print(f"Issue mise à jour sur GitHub : {issue['title']} - État : {data['state']}")
        return github_issue
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la mise à jour de l'issue sur GitHub : {e}")


def create_github_issue(issue):
    """Crée une issue sur GitHub."""
    url = f"https://api.github.com/repos/{HUB_REPO}/issues"
    data = {
        "title": issue["title"],
        "body": issue.get("description", "Pas de description"),  # Description sans l'ID
        "labels": issue.get("labels", [])  # Ajouter les labels
    }
    
    try:
        # Création de l'issue sur GitHub
        response = requests.post(url, headers=github_headers, json=data)
        response.raise_for_status()
        github_issue = response.json()

        # Ajout d'un commentaire avec l'ID de l'issue GitLab
        comment_url = f"https://api.github.com/repos/{HUB_REPO}/issues/{github_issue['number']}/comments"
        comment_data = {
            "body": f"GitLab Issue ID: {issue['iid']}"
        }
        comment_response = requests.post(comment_url, headers=github_headers, json=comment_data)
        comment_response.raise_for_status()
        
        print(f"Issue créée sur GitHub : {issue['title']}")
        return github_issue
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la création de l'issue sur GitHub : {e}")

# def update_gitlab_issue(issue, gitlab_issue):
#     """Met à jour une issue existante sur GitLab."""
#     url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue['iid']}"
    
#     # Extraire les noms des labels si ce sont des dictionnaires
#     labels = []
#     for label in issue.get("labels", []):
#         if isinstance(label, dict):
#             labels.append(label["name"])  # GitHub retourne des dictionnaires pour les labels
#         else:
#             labels.append(label)  # GitLab retourne directement des chaînes de caractères
    
#     data = {
#         "title": issue["title"],
#         "description": issue.get("body", issue.get("description", "Pas de description")),  # Utilisation de 'body' ou 'description'
#         "state_event": "close" if issue["state"] == "closed" else "reopen",
#         "labels": ",".join(labels)  # Joindre les labels en une seule chaîne
#     }

#     if gitlab_issue["iid"] != issue["title"] and gitlab_issue["description"] != issue["body"] and gitlab_issue["state_event"] != convert_state_for_gitlab(issue["state"]):
    
#         try:
#             # Mise à jour de l'issue sur GitLab
#             response = requests.put(url, headers=gitlab_headers, json=data, verify=False)
#             response.raise_for_status()
#             gitlab_issue = response.json()
            
#             # Ajout d'un commentaire avec l'ID de l'issue GitHub
#             comment_url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue['iid']}/notes"
#             comment_data = {
#                 "body": f"GitHub Issue ID: {issue['number']}"
#             }
#             comment_response = requests.post(comment_url, headers=gitlab_headers, json=comment_data, verify=False)
#             comment_response.raise_for_status()
            
#             print(f"Issue mise à jour sur GitLab : {issue['title']} - État : {data['state_event']}")
#             return gitlab_issue
#         except requests.exceptions.RequestException as e:
#             print(f"Erreur lors de la mise à jour de l'issue sur GitLab : {e}")
def update_gitlab_issue(issue, gitlab_issue):
    """Met à jour une issue existante sur GitLab et ajoute l'ID GitHub en commentaire."""
    url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue['iid']}"
    
    # Extraire les noms des labels
    labels = []
    for label in issue.get("labels", []):
        if isinstance(label, dict):
            labels.append(label["name"])  # GitHub retourne des dictionnaires
        else:
            labels.append(label)  # GitLab retourne des strings

    data = {
        "title": issue["title"],
        "description": issue.get("body", issue.get("description", "Pas de description")),
        "state_event": "close" if issue["state"] == "closed" else "reopen",
        "labels": ",".join(labels),
    }

    try:
        # Mise à jour de l'issue sur GitLab
        response = requests.put(url, headers=gitlab_headers, json=data, verify=False)
        response.raise_for_status()
        updated_gitlab_issue = response.json()

        # Vérifier si le commentaire avec l'ID GitHub existe déjà
        gitlab_comments = get_gitlab_comments(gitlab_issue['iid'])
        github_id_comment_exists = any(
            f"GitHub Issue ID: {issue['number']}" in comment["body"]
            for comment in gitlab_comments
        )

        # Ajouter le commentaire seulement s'il n'existe pas
        if not github_id_comment_exists:
            comment_url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue['iid']}/notes"
            comment_data = {"body": f"GitHub Issue ID: {issue['number']}"}
            requests.post(comment_url, headers=gitlab_headers, json=comment_data, verify=False)

        print(f"Issue mise à jour sur GitLab : {issue['title']}")
        return updated_gitlab_issue
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la mise à jour de l'issue sur GitLab : {e}")

# def create_gitlab_issue(issue):
#     """Crée une issue sur GitLab et ajoute un commentaire avec l'ID de l'issue GitHub."""
#     url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues"
#     data = {
#         "title": issue["title"],
#         "description": issue.get("body", "Pas de description"),  # Description sans l'ID
#         "state_event": convert_state_for_gitlab(issue["state"]),  # Convert state for GitLab
#         "labels": ",".join(issue.get("labels", []))  # Ajouter les labels
#     }
    
#     try:
#         # Création de l'issue sur GitLab
#         response = requests.post(url, headers=gitlab_headers, json=data, verify=False)
#         response.raise_for_status()
#         gitlab_issue = response.json()
        
#         # Ajout d'un commentaire avec l'ID de l'issue GitHub
#         comment_url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue['iid']}/notes"
#         comment_data = {
#             "body": f"GitHub Issue ID: {issue['number']}"
#         }
#         comment_response = requests.post(comment_url, headers=gitlab_headers, json=comment_data, verify=False)
#         comment_response.raise_for_status()
        
#         print(f"Issue créée sur GitLab : {issue['title']} - État : {data['state_event']}")
#         return gitlab_issue
#     except requests.exceptions.RequestException as e:
#         print(f"Erreur lors de la création de l'issue sur GitLab : {e}")
def create_gitlab_issue(issue):
    """Crée une issue sur GitLab et ajoute un commentaire avec l'ID GitHub."""
    url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues"
    data = {
        "title": issue["title"],
        "description": issue.get("body", "Pas de description"),
        "state_event": convert_state_for_gitlab(issue["state"]),
        "labels": ",".join(issue.get("labels", [])),
    }
    
    try:
        # Création de l'issue sur GitLab
        response = requests.post(url, headers=gitlab_headers, json=data, verify=False)
        response.raise_for_status()
        gitlab_issue = response.json()

        # Ajout du commentaire avec l'ID GitHub
        comment_url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue['iid']}/notes"
        comment_data = {"body": f"GitHub Issue ID: {issue['number']}"}
        requests.post(comment_url, headers=gitlab_headers, json=comment_data, verify=False)

        print(f"Issue créée sur GitLab : {issue['title']}")
        return gitlab_issue
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la création de l'issue sur GitLab : {e}")

IGNORED_PHRASES = ["changed the description"]  # Liste des phrases à ignorer
def create_github_comment(issue_number, comment):
    url = f"https://api.github.com/repos/{HUB_REPO}/issues/{issue_number}/comments"
    data = {"body": comment}
    response = requests.post(url, headers=github_headers, json=data)
    response.raise_for_status()

def create_gitlab_comment(issue_iid, comment):
    url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{issue_iid}/notes"
    data = {"body": comment}
    response = requests.post(url, headers=gitlab_headers, json=data, verify=False)
    response.raise_for_status()


def normalize_comment_body(body):
    """Nettoie le contenu du commentaire pour éviter des duplications inutiles."""
    # Supprime les espaces inutiles, uniformise les sauts de ligne et met en minuscule
    return " ".join(body.strip().split()).lower()

def is_response_comment(body):
    """Détermine si un commentaire est une réponse à un autre."""
    return body.strip().startswith("@")  # Identifie les réponses via '@'

def sync_comments(github_issue, gitlab_issue):
    """Synchronise les commentaires entre une issue GitHub et une issue GitLab."""
    github_comments = get_github_comments(github_issue["number"])
    gitlab_comments = get_gitlab_comments(gitlab_issue["iid"])

    

    # Normaliser et filtrer les commentaires à ignorer
    github_comment_bodies = {
        normalize_comment_body(comment["body"]): comment
        for comment in github_comments
        if not any(phrase in comment["body"] for phrase in IGNORED_PHRASES)
        and not is_response_comment(comment["body"])
    }
    gitlab_comment_bodies = {
        normalize_comment_body(comment["body"]): comment
        for comment in gitlab_comments
        if not any(phrase in comment["body"] for phrase in IGNORED_PHRASES)
        and not is_response_comment(comment["body"])
    }

    # Identifier les commentaires qui ne sont pas encore synchronisés
    unsynced_github_to_gitlab = {
        body: comment for body, comment in github_comment_bodies.items()
        if body not in gitlab_comment_bodies
    }
    unsynced_gitlab_to_github = {
        body: comment for body, comment in gitlab_comment_bodies.items()
        if body not in github_comment_bodies
    }

    # Synchroniser les commentaires GitHub → GitLab
    for body, github_comment in unsynced_github_to_gitlab.items():
        print(f"Synchronisation du commentaire GitHub vers GitLab : {body}")
        create_gitlab_comment(gitlab_issue["iid"], github_comment["body"])


    # Synchroniser les commentaires GitLab → GitHub
    for body, gitlab_comment in unsynced_gitlab_to_github.items():
        print(f"Synchronisation du commentaire GitLab vers GitHub : {body}")
        create_github_comment(github_issue["number"], gitlab_comment["body"])

synced_comments = {
    "github": {},  # ID de commentaire GitHub : timestamp
    "gitlab": {}   # ID de commentaire GitLab : timestamp
}

def sync_comments(gitlab_issue_id, github_issue_number):
    """Synchronise les commentaires entre GitLab et GitHub."""
    gitlab_comments_url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue_id}/notes"
    github_comments_url = f"https://api.github.com/repos/{HUB_REPO}/issues/{github_issue_number}/comments"

    # Récupérer les commentaires des deux plateformes
    gitlab_comments = requests.get(gitlab_comments_url, headers=gitlab_headers, verify=False).json()
    github_comments = requests.get(github_comments_url, headers=github_headers).json()

    # Filtrer les commentaires (exclure les IDs externes et les phrases ignorées)
    def filter_comments(comments, platform):
        filtered = []
        for comment in comments:
            body = comment.get("body", "")
            # Exclure les commentaires générés par le script
            if platform == "gitlab":
                if "GitHub Issue ID:" in body: continue
            elif platform == "github":
                if "GitLab Issue ID:" in body: continue
            # Exclure les phrases ignorées (comme les modifications de description)
            if any(phrase in body for phrase in IGNORED_PHRASES): continue
            filtered.append(comment)
        return filtered

    gitlab_filtered = filter_comments(gitlab_comments, "gitlab")
    github_filtered = filter_comments(github_comments, "github")

    # Synchroniser GitLab → GitHub
    trouve = 0
    for comment in gitlab_filtered:
        comment_body = comment["body"]
        # Vérifier si le commentaire existe déjà sur GitHub
        if not any(c["body"] == comment_body for c in github_filtered):
            create_github_comment(github_issue_number, comment_body)

    # Synchroniser GitHub → GitLab
    for comment in github_filtered:
        comment_body = comment["body"]
        # Vérifier si le commentaire existe déjà sur GitLab
        if not any(c["body"] == comment_body for c in gitlab_filtered):
            create_gitlab_comment(gitlab_issue_id, comment_body)
            trouve = 1
    if trouve:
        print("Commentaires synchronisés sans duplication.")
    else:
        print("Commentaires sont à jour.")


# def sync_comments(gitlab_issue_id, github_issue_number):
#     """Synchronise les commentaires entre GitLab et GitHub."""
#     gitlab_comments_url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{gitlab_issue_id}/notes"
#     github_comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{github_issue_number}/comments"

#     # Récupérer les commentaires des deux plateformes
#     gitlab_comments = requests.get(gitlab_comments_url, headers=gitlab_headers, verify=False).json()
#     github_comments = requests.get(github_comments_url, headers=github_headers).json()

#     # Filtrer les commentaires (exclure les IDs externes et les phrases ignorées)
#     def filter_comments(comments, platform):
#         filtered = []
#         for comment in comments:
#             body = comment.get("body", "")
#             # Exclure les commentaires générés par le script
#             if platform == "gitlab":
#                 if "GitHub Issue ID:" in body: continue
#             elif platform == "github":
#                 if "GitLab Issue ID:" in body: continue
#             # Exclure les phrases ignorées (comme les modifications de description)
#             if any(phrase in body for phrase in IGNORED_PHRASES): continue
#             filtered.append(comment)
#         return filtered

#     gitlab_filtered = filter_comments(gitlab_comments, "gitlab")
#     github_filtered = filter_comments(github_comments, "github")

#     # Synchroniser GitLab → GitHub
#     for comment in gitlab_filtered:
#         comment_body = comment["body"]
#         # Vérifier si le commentaire existe déjà sur GitHub
#         if not any(c["body"] == comment_body for c in github_filtered):
#             create_github_comment(github_issue_number, comment_body)

#     # Synchroniser GitHub → GitLab
#     for comment in github_filtered:
#         comment_body = comment["body"]
#         # Vérifier si le commentaire existe déjà sur GitLab
#         if not any(c["body"] == comment_body for c in gitlab_filtered):
#             create_gitlab_comment(gitlab_issue_id, comment_body)

#     print("Commentaires synchronisés sans duplication.")


def get_github_comments(issue_number):
    url = f"https://api.github.com/repos/{HUB_REPO}/issues/{issue_number}/comments"
    response = requests.get(url, headers=github_headers)
    response.raise_for_status()
    return response.json()

def get_gitlab_comments(issue_iid):
    url = f"{GITLAB_URL}/projects/{GITLAB_PROJECT_ID}/issues/{issue_iid}/notes"
    response = requests.get(url, headers=gitlab_headers, verify=False)
    response.raise_for_status()
    return response.json()

def sync_bidirectional_issues():
    """Synchronise les issues dans les deux sens entre GitHub et GitLab."""
    github_issues = get_github_issues()
    gitlab_issues = get_gitlab_issues()

    # Synchroniser les milestones avant de traiter les issues
    sync_milestones()

    github_issues_by_gitlab_id = {
        extract_external_id(get_github_comments(issue["number"]), "GitHub"): issue
        for issue in github_issues
        if extract_external_id(get_github_comments(issue["number"]), "GitHub")
    }

    gitlab_issues_by_github_id = {
        extract_external_id(get_gitlab_comments(issue["iid"]), "GitLab"): issue
        for issue in gitlab_issues
        if extract_external_id(get_gitlab_comments(issue["iid"]), "GitLab")
    }

    # Synchronisation GitHub → GitLab
    for issue in github_issues:
        github_id = str(issue["number"])
        if github_id in gitlab_issues_by_github_id:
            print("gitlab_id 2", github_id)

            gitlab_issue = gitlab_issues_by_github_id[github_id]
            # Vérifiez si l'état ou la description a changé
            if (gitlab_issue["description"] != issue.get("body", "Pas de description") or
                    gitlab_issue["state"] != issue["state"]):
                #update_gitlab_issue(issue, gitlab_issue["iid"])
                print("etape 1")
                sync_comments(gitlab_issue["iid"], issue["number"])

            # Synchroniser le milestone
            if issue.get("milestone"):
                milestone_title = issue["milestone"]["title"]
                update_gitlab_issue_with_milestone(issue, gitlab_issue, milestone_title)
        else:
            # Vérifier si une issue avec le même titre existe déjà
            existing_gitlab_issue = next((i for i in gitlab_issues if i["title"] == issue["title"]), None)

            if not existing_gitlab_issue:
                created_gitlab_issue = create_gitlab_issue(issue)
                update_github_issue(created_gitlab_issue, issue["number"])
                print("etape 2")
                sync_comments(created_gitlab_issue['iid'], issue["number"])

                # Synchroniser le milestone
                if issue.get("milestone"):
                    milestone_title = issue["milestone"]["title"]
                    update_gitlab_issue_with_milestone(issue, created_gitlab_issue, milestone_title)
                    
    # Synchronisation GitLab → GitHub
    for issue in gitlab_issues:
        github_id = extract_external_id(get_gitlab_comments(issue["iid"]), "GitLab")
        if github_id and github_id in github_issues_by_gitlab_id:
            github_issue = github_issues_by_gitlab_id[github_id]
            # Vérifiez si l'état ou la description a changé
            if (github_issue["body"] != issue["description"] or
                    github_issue["state"] != issue["state"]):
                #update_github_issue(issue, github_issue["number"])
                print("etape 3")
                sync_comments(issue["iid"], github_issue["number"])

            # Synchroniser le milestone
            if issue.get("milestone"):
                milestone_title = issue["milestone"]["title"]
                update_github_issue_with_milestone(issue, github_issue, milestone_title)
        else:
            # Vérifier si une issue avec le même titre existe déjà
            existing_github_issue = next((i for i in github_issues if i["title"] == issue["title"]), None)
            if not existing_github_issue:
                created_github_issue = create_github_issue(issue)
                update_gitlab_issue(created_github_issue, issue)
                print("etape 4")
                sync_comments(issue["iid"], created_github_issue["number"])

                # Synchroniser le milestone
                if issue.get("milestone"):
                    milestone_title = issue["milestone"]["title"]
                    update_github_issue_with_milestone(issue, created_github_issue, milestone_title)
                

if __name__ == "__main__":
    sync_bidirectional_issues()
