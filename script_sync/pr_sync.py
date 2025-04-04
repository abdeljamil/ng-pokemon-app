
#SERVEUR LOCAL GITLAB

# -*- coding: utf-8 -*-
import os
import subprocess
import shutil
import stat
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fonction pour forcer la suppression des fichiers verrouillés sous Windows
def remove_readonly(func, path, _):
    """ Supprime l'attribut 'lecture seule' des fichiers et les supprime. """
    os.chmod(path, stat.S_IWRITE)
    func(path)



# github_clone_url = f"https://{github_token}@github.com/{github_repo}.git"
# gitlab_clone_url = f"https://oauth2:{gitlab_token}@192.168.0.244/{gitlab_repo_path}.git"

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
HUB_TOKEN = os.getenv("HUB_TOKEN") 
HUB_REPO = os.getenv("HUB_REPO")
GITLAB_REPO = os.getenv("GITLAB_REPO")

github_clone_url = f"https://{HUB_TOKEN}@github.com/{HUB_REPO}.git"
gitlab_clone_url = f"https://oauth2:{GITLAB_TOKEN}@192.168.0.244/{GITLAB_REPO}.git"

print(f"HUB_TOKEN: {HUB_TOKEN}")
print(f"HUB_REPO: {HUB_REPO}")


# # Dossier temporaire pour la synchronisation
temp_dir = "repo_sync"

# # Supprimer l'ancien dossier si existant
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir, onerror=remove_readonly)

# # Cloner depuis GitLab pour garder ses modifications
subprocess.run(["git", "clone", gitlab_clone_url, temp_dir], check=True)

# # Ajouter GitHub comme remote
os.chdir(temp_dir)
subprocess.run(["git", "remote", "add", "github", github_clone_url], check=True)

# # Récupérer toutes les branches des deux dépôts
subprocess.run(["git", "fetch", "--all"], check=True)

# # Lister toutes les branches distantes (exclure les lignes avec "->")

def get_remote_branches(remote):
    result = subprocess.run(["git", "branch", "-r"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
        print(f"❌ Erreur lors de l'exécution de git branch -r: {result.stderr}")
        return []
    
    branches = [
        line.strip().split("/", 1)[1]  # Extraire le nom de la branche
        for line in result.stdout.splitlines()
        if line.strip().startswith(remote) and "->" not in line  # Exclure les lignes avec "->"
    ]
    return branches

gitlab_branches = get_remote_branches("origin")
github_branches = get_remote_branches("github")

# Synchroniser toutes les branches
for branch in set(gitlab_branches + github_branches):
    print(f"⏳ Synchronisation de la branche : {branch}")

    # Vérifier si la branche existe sur GitLab
    if branch not in gitlab_branches:
        print(f"🚀 Création de la branche {branch} sur GitLab")
        try:
            # Créer la branche locale à partir de la branche distante GitHub
            subprocess.run(["git", "checkout", "-b", branch, f"github/{branch}"], check=True)
            # Pousser la branche vers GitLab
            subprocess.run(["git", "push", "origin", branch], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de la création de la branche {branch} sur GitLab : {e}")
    # Vérifier si la branche existe sur GitHub
    elif branch not in github_branches:
        print(f"🚀 Création de la branche {branch} sur GitHub")
        try:
            # Créer la branche locale à partir de la branche distante GitLab
            subprocess.run(["git", "checkout", "-b", branch, f"origin/{branch}"], check=True)
            # Pousser la branche vers GitHub
            subprocess.run(["git", "push", "github", branch], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de la création de la branche {branch} sur GitHub : {e}")
    else:
        # Synchroniser les modifications entre les deux dépôts
        print(f"🔄 Fusion des modifications pour la branche : {branch}")
        try:
            # Vérifier si la branche distante existe avant de créer une branche locale
            if subprocess.run(["git", "show-ref", "--verify", f"refs/remotes/origin/{branch}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).returncode == 0:
                # Créer une branche locale si elle n'existe pas
                if not subprocess.run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).returncode == 0:
                    print(f"🚀 Création de la branche locale : {branch}")
                    subprocess.run(["git", "checkout", "-b", branch, f"origin/{branch}"], check=True)
                # Synchroniser les modifications
                subprocess.run(["git", "checkout", branch], check=True)
                subprocess.run(["git", "pull", "origin", branch], check=True)  # Mettre à jour depuis GitLab
                subprocess.run(["git", "pull", "github", branch], check=True)  # Mettre à jour depuis GitHub
                subprocess.run(["git", "push", "origin", branch], check=True)  # Pousser vers GitLab
                subprocess.run(["git", "push", "github", branch], check=True)  # Pousser vers GitHub
            else:
                print(f"⚠️ La branche distante 'origin/{branch}' n'existe pas. Ignorer cette branche.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de la synchronisation de la branche {branch}: {e}")

print("✅ Synchronisation bidirectionnelle terminée avec succès pour toutes les branches !")
